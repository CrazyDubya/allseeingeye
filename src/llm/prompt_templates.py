#!/usr/bin/env python3
"""
Prompt templates for AllSeeingEye LLM integration
"""


class PromptTemplates:
    """Collection of optimized prompt templates for various analysis tasks"""
    
    # Basic code analysis template
    CODE_ANALYSIS = """
    You are an expert code analyzer tasked with examining the following {language} code.
    
    FILENAME: {filename}
    
    ```{language}
    {code}
    ```
    
    Analyze this code and provide:
    
    1. A concise summary of the code's purpose and functionality
    2. The key components and their responsibilities
    3. Any notable patterns, algorithms, or techniques used
    4. Potential issues or areas for improvement
    
    Format your response as clearly structured markdown.
    """
    
    # Code review template
    CODE_REVIEW = """
    You are an expert software engineer reviewing the following {language} code.
    
    FILENAME: {filename}
    
    ```{language}
    {code}
    ```
    
    Conduct a thorough code review covering:
    
    1. Code quality (clarity, readability, maintainability)
    2. Architectural patterns and design principles
    3. Potential bugs, edge cases, or error handling issues
    4. Performance considerations
    5. Security vulnerabilities or concerns
    
    For each issue found, provide:
    - The specific line or section
    - A clear description of the issue
    - A recommended solution or improvement
    
    Format your review as a markdown document with clear sections.
    """
    
    # Codebase structure analysis template
    CODEBASE_STRUCTURE = """
    You are an expert software architect analyzing the structure of a codebase.
    
    DIRECTORY STRUCTURE:
    ```
    {structure}
    ```
    
    Analyze this codebase structure and provide:
    
    1. An overview of the apparent architecture
    2. The main components and their likely responsibilities
    3. Patterns in the project organization
    4. Suggestions for improving the structure
    
    Consider how the files and directories relate to each other and what architecture pattern this suggests.
    Format your analysis as a clearly structured markdown document.
    """
    
    # Improvement recommendations template
    IMPROVEMENT_RECOMMENDATIONS = """
    You are an expert software consultant providing recommendations for improving a codebase.
    
    CODEBASE STATISTICS:
    - Total files: {file_count}
    - File categories: {file_categories}
    - Total lines of code: {line_count}
    - Languages used: {languages}
    
    Based on this information and the following context:
    
    ```
    {context}
    ```
    
    Provide {recommendation_count} strategic recommendations for improving this codebase.
    
    For each recommendation:
    1. Provide a clear title
    2. Describe the recommendation in detail
    3. Explain the expected benefits
    4. Estimate the implementation complexity (Low, Medium, High)
    5. Suggest concrete steps for implementation
    
    Format your response as a JSON object with the following structure:
    ```json
    {{
      "recommendations": [
        {{
          "title": "Recommendation Title",
          "description": "Detailed description",
          "benefits": "Expected benefits",
          "complexity": "Low|Medium|High",
          "implementation_steps": ["Step 1", "Step 2", ...]
        }},
        ...
      ]
    }}
    ```
    
    Ensure your response is valid JSON.
    """
    
    # Documentation generation template
    DOCUMENTATION = """
    You are an expert technical writer generating documentation for the following {language} code.
    
    FILENAME: {filename}
    
    ```{language}
    {code}
    ```
    
    Generate comprehensive documentation for this code, including:
    
    1. A high-level overview
    2. Detailed explanation of each function/class/component
    3. Parameters, return values, and their types
    4. Usage examples
    5. Dependencies and requirements
    
    Format your documentation as markdown, suitable for inclusion in a project README or documentation site.
    """
    
    # Bug analysis template
    BUG_ANALYSIS = """
    You are an expert debugging engineer analyzing a potential bug in the following {language} code.
    
    FILENAME: {filename}
    
    ```{language}
    {code}
    ```
    
    ERROR/ISSUE DESCRIPTION:
    {issue_description}
    
    Analyze this code and:
    
    1. Identify potential causes of the described issue
    2. Explain the most likely root cause
    3. Suggest fixes for the identified problems
    4. Recommend testing approaches to verify the fix
    
    Be specific about line numbers and code sections in your analysis.
    Format your response as a clearly structured markdown document.
    """
    
    # Security audit template
    SECURITY_AUDIT = """
    You are an expert security auditor reviewing the following {language} code for security vulnerabilities.
    
    FILENAME: {filename}
    
    ```{language}
    {code}
    ```
    
    Perform a comprehensive security audit, looking for:
    
    1. Input validation issues
    2. Authentication/authorization flaws
    3. Data handling vulnerabilities
    4. Common security anti-patterns
    5. Language-specific security concerns
    
    For each vulnerability found:
    - Provide the specific line or section
    - Describe the vulnerability and potential exploit
    - Assign a severity (Low, Medium, High, Critical)
    - Recommend a secure implementation
    
    Format your audit as a markdown document with clearly defined sections.
    """
    
    # Performance analysis template
    PERFORMANCE_ANALYSIS = """
    You are an expert performance engineer analyzing the following {language} code for efficiency issues.
    
    FILENAME: {filename}
    
    ```{language}
    {code}
    ```
    
    Analyze this code for performance considerations:
    
    1. Algorithmic efficiency
    2. Resource usage (memory, CPU, I/O)
    3. Bottlenecks and hot spots
    4. Scalability concerns
    
    For each issue identified:
    - Specify the line or section
    - Explain the performance impact
    - Suggest optimizations
    - Estimate the improvement potential
    
    Format your analysis as a clearly structured markdown document.
    """
    
    # Test case generation template
    TEST_CASE_GENERATION = """
    You are an expert QA engineer generating test cases for the following {language} code.
    
    FILENAME: {filename}
    
    ```{language}
    {code}
    ```
    
    Generate a comprehensive test suite for this code, including:
    
    1. Unit tests for individual functions/methods
    2. Edge case tests
    3. Integration tests (if applicable)
    4. Performance tests (if applicable)
    
    For each test case:
    - Describe the test purpose
    - Specify inputs and expected outputs
    - Identify edge cases to be tested
    
    If possible, provide actual test code that could be implemented using a standard testing framework for {language}.
    Format your response as a markdown document with clearly separated test cases.
    """
