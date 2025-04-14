import os
import json
import sys
from mistralai import Mistral

class MistralAnalyzer:
    def __init__(self):
        """Initialize Mistral client with API key."""
        self.api_key = os.getenv('MISTRAL_API_KEY')
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        self.client = Mistral(api_key=self.api_key)
        self.agent_id = "ag:0dd6ad20:20250414:foia-checker:2ac12c27"

    def _debug_print(self, message, data=None):
        """Print debug information in a consistent format."""
        print("\n=== DEBUG ===", file=sys.stderr)
        print(message, file=sys.stderr)
        if data:
            print(json.dumps(data, indent=2), file=sys.stderr)
        print("=============\n", file=sys.stderr)

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
                - refined_text (dict): Improved version of the request in legal French
        """
        try:
            # Format the request items for analysis
            items = {}
            for i, item in enumerate(request_data['description'], 1):
                item_key = f"Item {i}:"
                items[item_key] = {
                    "description": item.get('description', ''),
                    "date": item.get('date', '')
                }
            
            # Create a clean request object
            request_obj = {
                "administration": request_data['administration'],
                "request_type": request_data['request_type'],
                "items": items
            }
            
            # Convert to JSON string for the agent
            request_json = json.dumps(request_obj, indent=2)
            self._debug_print("Sending request to agent:", request_obj)
            
            # Use the agent to analyze the request
            response = self.client.agents.complete(
                agent_id=self.agent_id,
                messages=[
                    {
                        "role": "user",
                        "content": request_json
                    }
                ]
            )
            
            # Parse the response
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                self._debug_print("Raw response from agent:", {"content": content})
                
                try:
                    # Try to parse the response as JSON
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
                    
                    self._debug_print("Parsed analysis:", analysis)
                    return analysis
                except json.JSONDecodeError as e:
                    self._debug_print("Failed to parse JSON response", {"error": str(e)})
                    return self._parse_analysis(content)
                except Exception as e:
                    self._debug_print("Error parsing response", {"error": str(e)})
                    return self._parse_analysis(content)
            else:
                self._debug_print("Unexpected response format", {"response": str(response)})
                raise ValueError("Unexpected response format from Mistral API")
                
        except Exception as e:
            self._debug_print("Error in analyze_request", {"error": str(e)})
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
        user_prompt = f"""
        Generate a {template_type} FOIA request in French with these details:
        Administration: {request_data['administration']}
        Request Type: {request_data['request_type']}
        Description: {request_data['description']}
        Response Format: {request_data.get('response_format', 'email')}
        """
        
        # Use the agent to generate the French text
        response = self.client.agents.complete(
            agent_id=self.agent_id,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        
        if hasattr(response, 'choices') and response.choices:
            return response.choices[0].message.content.strip()
        else:
            raise ValueError("Unexpected response format from Mistral API") 