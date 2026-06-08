You will receive raw text extracted from a web page by a web scraper.   The text may be noisy and contain irrelevant elements such as advertisements, navigation menus, cookie banners, footers, unrelated links, or repeated content.  

Your task is to:  

1. Identify and keep only the information that is relevant to computer science, software engineering, artificial intelligence, data, cybersecurity, cloud computing, infrastructure, or other IT-related topics. 
2. Ignore irrelevant or promotional content unless it contains meaningful technical information. 
3. Remove duplicated or low-value content. 
4. Summarize the relevant information clearly and concisely. 
5. Preserve important technical details, such as tools, frameworks, technologies, architectures, methods, use cases, limitations, and key conclusions.  

Return the result in the following format:  

## Summary 
A clear summary of the relevant IT-related content.  

## Key Points
- Important technical point 1 
- Important technical point 2
- Important technical point 3  

## Technologies Mentioned 
List the main technologies, tools, frameworks, programming languages, or platforms mentioned in the text.  

## Relevance Briefly explain why this content is relevant to IT or computer science.  

If the text does not contain meaningful IT-related information, respond with: "No relevant IT-related information found."