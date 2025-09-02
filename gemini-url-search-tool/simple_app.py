#!/usr/bin/env python3
"""
Simple Streamlit app for testing - Gemini URL Search Tool
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Simple main application"""
    st.set_page_config(
        page_title="Gemini URL Search Tool",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Gemini URL Search Tool")
    st.markdown("---")
    
    # Check API key and debug mode
    api_key = os.getenv("GEMINI_API_KEY")
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    if not api_key:
        st.error("⚠️ Gemini API key not configured")
        st.markdown("""
        Please set up your API key:
        1. Copy `.env.example` to `.env`
        2. Add your Gemini API key to the `.env` file
        3. Restart the application
        """)
        return
    
    st.success("✅ API key configured")
    
    # Debug mode toggle
    if st.checkbox("🐛 Enable Debug Mode", value=debug_mode):
        debug_mode = True
    
    # Simple search interface
    st.subheader("🔍 Search Interface")
    
    search_type = st.selectbox(
        "Search Type",
        ["General Search", "Component Search"],
        help="Choose the type of search you want to perform"
    )
    
    if search_type == "General Search":
        keywords = st.text_input(
            "Keywords",
            placeholder="Enter keywords to search for...",
            help="Enter keywords or phrases to search for"
        )
        
        if st.button("🔍 Search", type="primary"):
            if keywords:
                with st.spinner("Searching with Gemini AI..."):
                    try:
                        # Import and use Gemini API
                        import google.generativeai as genai
                        
                        # Configure Gemini
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        # Create search prompt for realistic recommendations
                        search_prompt = f"""
                        Based on the search query "{keywords}", please suggest realistic and helpful resources.
                        
                        Provide 5 relevant resources with realistic URLs, titles and descriptions in JSON format:
                        {{
                            "results": [
                                {{
                                    "title": "Resource Title",
                                    "url": "realistic URL (like official docs, GitHub, Stack Overflow, etc.)",
                                    "description": "Brief description of what this resource provides"
                                }}
                            ]
                        }}
                        
                        Focus on well-known, authoritative sources like:
                        - Official documentation sites
                        - GitHub repositories
                        - Stack Overflow discussions
                        - Educational platforms (Coursera, edX, Udemy)
                        - Technical blogs and tutorials
                        
                        Make the URLs realistic and specific to the topic.
                        """
                        
                        # Get response from Gemini
                        response = model.generate_content(search_prompt)
                        
                        st.success(f"✅ Search completed for: {keywords}")
                        
                        # Display the raw response only in debug mode
                        if debug_mode:
                            st.subheader("🤖 Gemini AI Response (Debug)")
                            st.code(response.text, language="json")
                        
                        # Try to parse JSON if possible
                        try:
                            import json
                            import re
                            
                            # Extract JSON from response
                            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                            if json_match:
                                json_data = json.loads(json_match.group())
                                
                                st.subheader("📋 Parsed Results")
                                for i, result in enumerate(json_data.get('results', []), 1):
                                    with st.expander(f"Result {i}: {result.get('title', 'No Title')}"):
                                        st.write(f"**URL:** {result.get('url', 'No URL')}")
                                        st.write(f"**Description:** {result.get('description', 'No Description')}")
                        except:
                            st.info("Could not parse structured results, showing raw response above.")
                            
                    except Exception as e:
                        st.error(f"❌ Search failed: {str(e)}")
                        st.info("Make sure your Gemini API key is correctly set in the .env file")
                        
                        # Show sample results as fallback
                        st.subheader("📋 Sample Results (Fallback)")
                        for i in range(3):
                            with st.expander(f"Sample Result {i+1}: {keywords} - Example {i+1}"):
                                st.write(f"URL: https://example.com/result{i+1}")
                                st.write(f"Description: This is a sample description for {keywords} result {i+1}")
            else:
                st.warning("Please enter keywords to search")
    
    else:  # Component Search
        col1, col2 = st.columns(2)
        
        with col1:
            manufacturer = st.text_input(
                "Manufacturer",
                placeholder="e.g., Arduino, Texas Instruments",
                help="Enter the manufacturer name"
            )
        
        with col2:
            part_number = st.text_input(
                "Part Number",
                placeholder="e.g., UNO R3, LM358",
                help="Enter the part number"
            )
        
        if st.button("🔍 Search Components", type="primary"):
            if manufacturer and part_number:
                with st.spinner("Searching for component specifications with Gemini AI..."):
                    try:
                        # Import and use Gemini API
                        import google.generativeai as genai
                        
                        # Configure Gemini
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        # Create component search prompt for realistic resources
                        component_prompt = f"""
                        For the electronic component "{manufacturer} {part_number}", suggest realistic technical resources.
                        
                        Provide relevant resources with realistic URLs in JSON format:
                        {{
                            "results": [
                                {{
                                    "title": "Document Title",
                                    "url": "realistic URL (manufacturer website, distributors, etc.)",
                                    "description": "Brief description",
                                    "type": "datasheet|specification|manual|distributor"
                                }}
                            ]
                        }}
                        
                        Focus on realistic sources like:
                        - Official manufacturer websites (ti.com, arduino.cc, etc.)
                        - Electronic distributors (digikey.com, mouser.com, etc.)
                        - Technical documentation sites
                        - Component databases
                        
                        Make URLs specific and realistic for this component.
                        """
                        
                        # Get response from Gemini
                        response = model.generate_content(component_prompt)
                        
                        st.success(f"✅ Component search completed for: {manufacturer} {part_number}")
                        
                        # Display the raw response only in debug mode
                        if debug_mode:
                            st.subheader("🤖 Gemini AI Response (Debug)")
                            st.code(response.text, language="json")
                        
                        # Try to parse JSON if possible
                        try:
                            import json
                            import re
                            
                            # Extract JSON from response
                            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                            if json_match:
                                json_data = json.loads(json_match.group())
                                
                                st.subheader("🔧 Component Results")
                                for i, result in enumerate(json_data.get('results', []), 1):
                                    doc_type = result.get('type', 'document').title()
                                    with st.expander(f"{doc_type} {i}: {result.get('title', 'No Title')}"):
                                        st.write(f"**URL:** {result.get('url', 'No URL')}")
                                        st.write(f"**Type:** {doc_type}")
                                        st.write(f"**Description:** {result.get('description', 'No Description')}")
                        except:
                            st.info("Could not parse structured results, showing raw response above.")
                            
                    except Exception as e:
                        st.error(f"❌ Component search failed: {str(e)}")
                        st.info("Make sure your Gemini API key is correctly set in the .env file")
                        
                        # Show sample results as fallback
                        st.subheader("🔧 Sample Component Results (Fallback)")
                        with st.expander(f"{manufacturer} {part_number} - Sample Datasheet"):
                            st.write(f"URL: https://example.com/{manufacturer.lower()}/{part_number.lower()}")
                            st.write(f"Type: Official Datasheet")
                            st.write(f"Description: Sample specifications for {manufacturer} {part_number}")
            else:
                st.warning("Please enter both manufacturer and part number")
    
    # Configuration display
    st.markdown("---")
    with st.expander("📋 System Status"):
        st.write("**Environment Variables:**")
        st.write(f"- API Key: {'✅ Configured' if api_key else '❌ Not configured'}")
        st.write(f"- Debug Mode: {os.getenv('DEBUG', 'false')}")
        st.write(f"- Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
        
        st.write("**Directories:**")
        data_dir = Path("data")
        logs_dir = Path("logs")
        st.write(f"- Data Directory: {'✅ Exists' if data_dir.exists() else '❌ Missing'}")
        st.write(f"- Logs Directory: {'✅ Exists' if logs_dir.exists() else '❌ Missing'}")

if __name__ == "__main__":
    main()