import os
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

class MistralAnalyzer:
    def __init__(self):
        """Initialize Mistral client with API key."""
        self.api_key = os.getenv('MISTRAL_API_KEY')
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        self.client = MistralClient(api_key=self.api_key)
        self.model = "mistral-medium"  # or another appropriate model

    def analyze_request(self, request_data):
        """
        Analyze a FOIA request and provide suggestions and likelihood estimation.
        
        Args:
            request_data (dict): Dictionary containing request details
                - administration (str): Name of the administration
                - request_type (str): Type of request (document/explanation)
                - description (list): List of request items with descriptions
                
        Returns:
            dict: Analysis results including:
                - clarity_score (float): 0-1 score of request clarity
                - success_likelihood (str): High/Good/Moderate assessment
                - suggestions (list): List of improvement suggestions
                - refined_text (str): Improved version of the request in legal French
        """
        try:
            # Construct the prompt for request analysis
            system_prompt = """You are an expert in Luxembourg's Freedom of Information law, 
            specifically the law of September 14, 2018 on transparent and open administration.

            Analyze the following request and provide a JSON response with:
            1. A clarity score (0-1)
            2. A success likelihood estimate (High/Good/Moderate)
            3. Improvement suggestions for each item in English
            4. A refined version of just the specific line item in legal French

            To be compliant and effective, each item should:
            - Explicitly specify the requested documents or required explanation
            - Clearly reference relevant details (dates, titles, subjects)
            - Use formal and polite language appropriate for official correspondence
            - Be concise but sufficiently complete to allow easy identification by the administration
            - Comply with Luxembourg legal requirements
            - Avoid overly broad or vague requests
            - Include appropriate temporal references
            - Precisely identify the documents or information

            IMPORTANT: For the refined_text field, if there are multiple items, use a JSON object with keys for each item.
            If there is only one item, you can use a string.
            
            For example, with multiple items:
            
            "refined_text": {
                "Item 1:": "Rapport intitulé 'Test Doc 1' daté du 25 juin",
                "Item 2:": "Document intitulé 'Test Doc 2'"
            }
            
            Or with a single item:
            
            "refined_text": "Rapport intitulé 'Test Doc' daté du 25 juin"

            The refined_text should be direct references to documents, starting with document types or names.
            DO NOT start with "Je souhaite" or similar phrases.

            For suggestions, ALWAYS provide at least 3-4 specific improvement suggestions for each item, focusing on:
            - Adding missing details (names, dates, specific document types)
            - Improving clarity and precision
            - Making the request more legally compliant
            - Using more formal language

            Respond with a JSON object in this exact format:
            {
                "clarity_score": 0.5,
                "success_likelihood": "High",
                "suggestions": [
                    "Item 1:",
                    "- Specify the exact type of document requested",
                    "- Include the judge's full name",
                    "- Add a specific date range",
                    "- Use formal language"
                ],
                "refined_text": {
                    "Item 1:": "Dossier administratif relatif au licenciement du juge [nom complet], survenu en [date précise], comprenant la décision de licenciement, les rapports d'enquête et toute correspondance administrative y relative."
                }
            }"""
            
            # Format the request items for analysis
            items_text = ""
            for i, item in enumerate(request_data['description'], 1):
                items_text += f"\nItem {i}:\n"
                if item.get('description'):
                    items_text += f"Description: {item['description']}\n"
                if item.get('date'):
                    items_text += f"Date: {item['date']}\n"
            
            user_prompt = f"""
            Administration: {request_data['administration']}
            Request Type: {request_data['request_type']}
            Request Items:{items_text}
            """
            
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]
            
            # Get analysis from Mistral
            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            
            # Parse the response
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                print("Raw response content:", content)  # Debug print
                
                try:
                    # Try to parse the response as JSON
                    import json
                    import re
                    
                    # Clean up the content to ensure it's valid JSON
                    # Find the JSON object within the response - look for the outermost curly braces
                    json_match = re.search(r'({[\s\S]*})', content)
                    if json_match:
                        json_str = json_match.group(1)
                        # Remove any markdown code block markers
                        json_str = re.sub(r'```json|```', '', json_str).strip()
                        # Fix invalid escape sequences like \_
                        json_str = json_str.replace('\\_', '_')
                        analysis = json.loads(json_str)
                    else:
                        # If no JSON object found, try the whole content after cleaning
                        json_str = content.strip()
                        # Remove any markdown code block markers
                        json_str = re.sub(r'```json|```', '', json_str).strip()
                        # Fix invalid escape sequences like \_
                        json_str = json_str.replace('\\_', '_')
                        analysis = json.loads(json_str)
                    
                    # Validate the response structure
                    if not isinstance(analysis, dict):
                        raise ValueError("Response is not a JSON object")
                    
                    # Ensure required fields are present
                    required_fields = ['clarity_score', 'success_likelihood', 'suggestions', 'refined_text']
                    for field in required_fields:
                        if field not in analysis:
                            raise ValueError(f"Missing required field: {field}")
                    
                    # Normalize suggestions to ensure it's a flat list of strings
                    if 'suggestions' in analysis and isinstance(analysis['suggestions'], list):
                        original_suggestions = analysis['suggestions']
                        flat_suggestions = []
                        for item in original_suggestions:
                            if isinstance(item, str):
                                flat_suggestions.append(item.strip())
                            elif isinstance(item, dict):
                                # Handle the observed error format: [{"Item 1:": ["- suggestion 1", ...]}, ...]
                                for key, value in item.items():
                                    flat_suggestions.append(str(key).strip()) # Add the item key ("Item 1:")
                                    if isinstance(value, list):
                                        # Add the actual suggestions (which should be strings)
                                        flat_suggestions.extend([str(s).strip() for s in value if isinstance(s, str) and s.strip()])
                                    elif isinstance(value, str) and value.strip():
                                        flat_suggestions.append(value.strip())
                        analysis['suggestions'] = [s for s in flat_suggestions if s] # Filter out empty strings

                    # Validate suggestions format after normalization
                    if not (isinstance(analysis.get('suggestions'), list) and
                            all(isinstance(s, str) for s in analysis.get('suggestions', []))):
                        print("Suggestions format normalization failed or resulted in non-string list. Defaulting.")
                        analysis['suggestions'] = ['Error processing suggestions format. Please review manually.']
                    
                    # Ensure refined_text is properly formatted
                    if isinstance(analysis['refined_text'], str):
                        # If it's a string, try to parse it as JSON
                        try:
                            parsed = json.loads(analysis['refined_text'])
                            if isinstance(parsed, dict):
                                analysis['refined_text'] = parsed
                            else:
                                # If it's not a dict, wrap it in a dict with Item 1
                                analysis['refined_text'] = {'Item 1:': analysis['refined_text']}
                        except json.JSONDecodeError:
                            # If parsing fails, wrap it in a dict with Item 1
                            analysis['refined_text'] = {'Item 1:': analysis['refined_text']}
                    elif not isinstance(analysis['refined_text'], dict):
                        # If it's not a string or dict, convert to dict
                        analysis['refined_text'] = {'Item 1:': str(analysis['refined_text'])}
                    
                    # Ensure all item keys are properly formatted
                    if isinstance(analysis['refined_text'], dict):
                        formatted_refined_text = {}
                        for key, value in analysis['refined_text'].items():
                            # Clean up the key
                            clean_key = key.strip()
                            if not clean_key.startswith('Item'):
                                clean_key = f'Item {clean_key}:'
                            elif not clean_key.endswith(':'):
                                clean_key = f'{clean_key}:'
                            formatted_refined_text[clean_key] = value.strip()
                        analysis['refined_text'] = formatted_refined_text
                    
                    return analysis
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON response: {e}, falling back to text parsing")
                    return self._parse_analysis(content)
                except Exception as e:
                    print(f"Error parsing response: {e}")
                    return self._parse_analysis(content)
            else:
                print("Unexpected response format:", response)
                raise ValueError("Unexpected response format from Mistral API")
                
        except Exception as e:
            print(f"Error in analyze_request: {e}")
            return {
                'clarity_score': 0.5,
                'success_likelihood': 'Moderate',
                'suggestions': [
                    'Error analyzing the request. Please try again.',
                    f'Technical details: {str(e)}'
                ],
                'refined_text': 'Error generating improved text. Please review the original request.'
            }
    
    def _parse_analysis(self, response_text):
        """Parse the LLM response into structured analysis. 
           Assumes initial JSON parsing in analyze_request failed."""
        print("Parsing response text using fallback text parser:", response_text)
        
        # Directly call the text parser since JSON parsing already failed.
        return self._parse_text_response(response_text)

    def _parse_text_response(self, response_text):
        """Parse the response text when JSON parsing fails."""
        analysis = {
            'clarity_score': 0.5,
            'success_likelihood': 'Moderate',
            'suggestions': [],
            'refined_text': {}
        }
        
        try:
            lines = response_text.split('\n')
            current_section = None
            refined_text_lines = []
            refined_text_obj = {}
            current_item = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if 'clarity_score' in line.lower():
                    try:
                        score = float(line.split(':')[1].strip().strip(','))
                        analysis['clarity_score'] = min(max(score, 0), 1)
                    except:
                        pass
                elif 'success_likelihood' in line.lower():
                    likelihood = line.split(':')[1].strip().strip('"')
                    if likelihood in ['High', 'Good', 'Moderate']:
                        analysis['success_likelihood'] = likelihood
                elif 'suggestions' in line.lower():
                    current_section = 'suggestions'
                    analysis['suggestions'] = []
                elif 'refined_text' in line.lower():
                    current_section = 'refined_text'
                    if ':' in line:
                        refined_text = line.split(':', 1)[1].strip()
                        refined_text = refined_text.strip('"')
                        if len(refined_text) > 1 and refined_text != '{':
                            refined_text_lines.append(refined_text)
                elif current_section == 'suggestions':
                    if line.startswith('Item') or line.startswith('Élément'):
                        # This is an item header for suggestions
                        analysis['suggestions'].append(line.strip())
                        current_item = line.strip()
                    elif line.startswith('-') or line.startswith('*'):
                        analysis['suggestions'].append(line.strip('-* '))
                elif current_section == 'refined_text':
                    if line.startswith('Item') or line.startswith('Élément'):
                        # This is an item header for refined text
                        current_item = line.strip()
                    elif ':' in line and current_item:
                        # This could be a key-value pair for refined text
                        key, value = line.split(':', 1)
                        if value.strip() and len(value.strip()) > 1:
                            refined_text_obj[current_item or key.strip()] = value.strip()
                    elif line.strip() and not any(keyword in line.lower() for keyword in ['clarity', 'success', 'suggestions']):
                        if current_item:
                            # Add to the current item
                            if current_item in refined_text_obj:
                                refined_text_obj[current_item] += ' ' + line.strip()
                            else:
                                refined_text_obj[current_item] = line.strip()
                        else:
                            # Just a regular line for refined text
                            if len(line.strip()) > 1 and line.strip() != '{':
                                refined_text_lines.append(line.strip())
            
            # Set the refined text from collected data
            if refined_text_obj:
                # We found structured item data
                analysis['refined_text'] = refined_text_obj
            elif refined_text_lines:
                # Join all refined text lines - could be a single item
                combined_text = ' '.join(refined_text_lines)
                if len(analysis['suggestions']) > 0 and 'Item' in analysis['suggestions'][0]:
                    # If we have Item headers in suggestions, create a simple object
                    analysis['refined_text'] = {analysis['suggestions'][0]: combined_text}
                else:
                    analysis['refined_text'] = combined_text
            
            # If refined_text is still empty or invalid, use the original request
            if not analysis['refined_text'] or analysis['refined_text'] == '{}' or analysis['refined_text'] == '{':
                print("No valid refined_text found in response")
                analysis['refined_text'] = 'Error generating improved text. Please review the original request.'
            
            # Ensure suggestions from text parsing is a flat list of non-empty strings
            if 'suggestions' in analysis and isinstance(analysis['suggestions'], list):
                analysis['suggestions'] = [s for s in analysis['suggestions'] if isinstance(s, str) and s.strip()]
            else:
                 analysis['suggestions'] = ['Error parsing suggestions. Please review manually.']
            
            return analysis
        except Exception as e:
            print(f"Error parsing text response: {e}")
            # Default suggestions on text parsing error
            analysis['suggestions'] = ['Error parsing text response. Please review manually.']
            return analysis

    def generate_french_text(self, request_data, template_type='full'):
        """
        Generate French text for the FOIA request.
        
        Args:
            request_data (dict): Request details
            template_type (str): Type of template to use (full/opening/closing)
            
        Returns:
            str: Generated French text
        """
        system_prompt = """You are an expert in writing formal French FOIA requests for Luxembourg administrations.
        Generate a professional and legally compliant request text in French.
        Use formal language and appropriate administrative terminology."""
        
        user_prompt = f"""
        Generate a {template_type} FOIA request in French with these details:
        Administration: {request_data['administration']}
        Request Type: {request_data['request_type']}
        Description: {request_data['description']}
        Response Format: {request_data.get('response_format', 'email')}
        """
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]
        
        response = self.client.chat(
            model=self.model,
            messages=messages
        )
        
        return response.messages[0].content.strip() 