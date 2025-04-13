import os
from utils.mistral import MistralAnalyzer

def test_mistral_analyzer():
    """Test the Mistral analyzer with a sample request."""
    # Sample request data
    request_data = {
        'administration': 'ministry_justice',
        'request_type': 'document',
        'description': [
            {
                'date': 'January 2025',
                'description': 'the file where I can see why this judge was dismissed'
            }
        ]
    }
    
    try:
        # Initialize analyzer
        analyzer = MistralAnalyzer()
        print("✅ MistralAnalyzer initialized successfully")
        
        # Get analysis
        analysis = analyzer.analyze_request(request_data)
        print("\nAnalysis Results:")
        print(f"Clarity Score: {analysis['clarity_score']}")
        print(f"Success Likelihood: {analysis['success_likelihood']}")
        print("\nSuggestions:")
        for suggestion in analysis['suggestions']:
            print(f"- {suggestion}")
        print("\nRefined Text:")
        print(analysis['refined_text'])
        
        # Verify response structure
        required_fields = ['clarity_score', 'success_likelihood', 'suggestions', 'refined_text']
        for field in required_fields:
            if field not in analysis:
                print(f"❌ Missing required field: {field}")
            else:
                print(f"✅ Field {field} present")
        
        # Verify data types
        if not isinstance(analysis['clarity_score'], (int, float)):
            print("❌ clarity_score should be a number")
        if not isinstance(analysis['success_likelihood'], str):
            print("❌ success_likelihood should be a string")
        if not isinstance(analysis['suggestions'], list):
            print("❌ suggestions should be a list")
        if not isinstance(analysis['refined_text'], str):
            print("❌ refined_text should be a string")
            
    except ValueError as e:
        if "MISTRAL_API_KEY" in str(e):
            print("❌ MISTRAL_API_KEY environment variable is not set")
            print("Please set the environment variable and try again")
        else:
            print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_mistral_analyzer() 