import os
import re
from bs4 import BeautifulSoup
import html2text
from pathlib import Path

def clean_html_content(soup):
    """Remove unwanted elements from HTML"""
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()
    
    # Remove common navigation and UI elements
    unwanted_classes = ['nav', 'header', 'footer', 'sidebar', 'menu', 'breadcrumb', 'navigation']
    for class_name in unwanted_classes:
        for element in soup.find_all(class_=re.compile(class_name, re.I)):
            element.decompose()
    
    # Remove elements with common navigation IDs
    unwanted_ids = ['nav', 'header', 'footer', 'sidebar', 'menu', 'navigation']
    for id_name in unwanted_ids:
        for element in soup.find_all(id=re.compile(id_name, re.I)):
            element.decompose()
    
    return soup

def extract_main_content(soup):
    """Extract the main content from HTML"""
    # Try to find main content area in order of preference
    selectors = [
        'main',
        'article', 
        '[role="main"]',
        '.content',
        '.main-content',
        '.article-content',
        '.post-content',
        '.entry-content',
        '#content',
        '#main-content'
    ]
    
    for selector in selectors:
        main_content = soup.select_one(selector)
        if main_content:
            return main_content
    
    # Fallback: return body content
    body = soup.find('body')
    if body:
        return body
    
    return soup

def html_to_markdown(html_content):
    """Convert HTML to Markdown"""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0
    h.ignore_emphasis = False
    h.skip_internal_links = True
    
    return h.handle(html_content)

def process_html_file(file_path):
    """Process a single HTML file and convert to Markdown"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get title first
        title_elem = soup.find('title')
        if title_elem:
            title_text = title_elem.get_text().strip()
        else:
            # Try h1 as fallback
            h1 = soup.find('h1')
            title_text = h1.get_text().strip() if h1 else Path(file_path).stem.replace('-', ' ').title()
        
        # Clean unwanted elements
        soup = clean_html_content(soup)
        
        # Extract main content
        main_content = extract_main_content(soup)
        
        # Convert to markdown
        markdown_content = html_to_markdown(str(main_content))
        
        # Clean up markdown
        markdown_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown_content)
        markdown_content = markdown_content.strip()
        
        # Format final markdown with title
        final_markdown = f"# {title_text}\n\n{markdown_content}"
        
        return final_markdown
        
    except Exception as e:
        return f"Error processing file: {str(e)}"

# Execute batch processing
def run_batch_1():
    directory = "downloaded_html_jobnimbus"
    # nit rwfreggevnjvbejgbevn
    
    
    if not os.path.exists(directory):
        return f"Directory {directory} not found"
    
    html_files = [f for f in os.listdir(directory) if f.endswith('.html')]
    
    print(f"Found {len(html_files)} HTML files in {directory}")
    
    # Process first 5 files
    batch_files = html_files[41:45]
    processed_successfully = []
    errors = []
    
    for html_file in batch_files:
        html_path = os.path.join(directory, html_file)
        md_filename = html_file.replace('.html', '.md')
        md_path = os.path.join(directory, md_filename)
        
        print(f"Processing: {html_file}")
        
        markdown_content = process_html_file(html_path)
        
        if markdown_content and not markdown_content.startswith("Error"):
            try:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                processed_successfully.append(md_filename)
                print(f"✓ Created: {md_filename}")
            except Exception as e:
                errors.append(f"{html_file}: Failed to write - {str(e)}")
                print(f"✗ Failed to write: {html_file}")
        else:
            errors.append(f"{html_file}: {markdown_content}")
            print(f"✗ Failed to process: {html_file}")
    
    remaining_files = len(html_files) - 5
    
    return {
        'total_files': len(html_files),
        'processed': processed_successfully,
        'errors': errors,
        'remaining': max(0, remaining_files),
        'batch_complete': True
    }

# Run the batch
result = run_batch_1()
print("\n" + "="*50)
print("BATCH 1 PROCESSING SUMMARY")
print("="*50)
print(f"Total HTML files found: {result['total_files']}")
print(f"Successfully processed: {len(result['processed'])}")
print(f"Errors encountered: {len(result['errors'])}")
print(f"Files remaining: {result['remaining']}")

if result['processed']:
    print(f"\n✓ Successfully created:")
    for file in result['processed']:
        print(f"  - {file}")

if result['errors']:
    print(f"\n✗ Errors:")
    for error in result['errors']:
        print(f"  - {error}")

print(f"\nReady to proceed with next batch: {'Yes' if result['remaining'] > 0 else 'No (all files processed)'}")
       