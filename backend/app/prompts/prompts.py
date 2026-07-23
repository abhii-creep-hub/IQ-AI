RESUME_PARSING_PROMPT = """You are an expert resume parser. Extract ALL information from the following resume text.
Return a valid JSON object with the exact structure below. Do NOT include any text outside the JSON.

Resume Text:
{resume_text}

Return JSON with this exact structure:
{{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1-XXX-XXX-XXXX",
    "location": "City, State/Country",
    "linkedin_url": "linkedin.com/in/username or empty string",
    "github_url": "github.com/username or empty string",
    "portfolio_url": "portfolio URL or empty string",
    "total_experience_years": 0.0,
    "skills": ["skill1", "skill2", "skill3"],
    "education": [
        {{
            "institution": "University Name",
            "degree": "Degree",
            "field_of_study": "Field",
            "start_year": 2018,
            "end_year": 2022,
            "gpa": "3.8/4.0",
            "description": "Any additional details"
        }}
    ],
    "experience": [
        {{
            "company": "Company Name",
            "title": "Job Title",
            "location": "City, State",
            "start_date": "Jan 2022",
            "end_date": "Present",
            "is_current": "true",
            "description": "Job description and responsibilities",
            "achievements": ["Achievement 1", "Achievement 2"]
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Project description",
            "technologies": ["tech1", "tech2"],
            "url": "project URL",
            "github_url": "github URL"
        }}
    ],
    "certifications": [
        {{
            "name": "Certification Name",
            "issuer": "Issuing Organization",
            "date_obtained": "2023",
            "expiry_date": "2025",
            "credential_url": "credential URL"
        }}
    ],
    "languages": ["English", "Spanish"],
    "achievements": ["Achievement 1", "Achievement 2"]
}}

IMPORTANT: Return ONLY valid JSON. No markdown, no explanations."""

ATS_SCORING_PROMPT = """You are an ATS (Applicant Tracking System) expert. Analyze the candidate's profile against the job description.

Job Description:
{job_description}

Required Skills: {required_skills}
Preferred Skills: {preferred_skills}
Minimum Experience: {experience_min} years
Maximum Experience: {experience_max} years
Education Level: {education_level}

Candidate Profile:
Name: {candidate_name}
Skills: {candidate_skills}
Experience: {candidate_experience} years
Education: {candidate_education}
Projects: {candidate_projects}
Certifications: {candidate_certifications}

Return a valid JSON object:
{{
    "total_score": 85.5,
    "skills_score": 90.0,
    "experience_score": 80.0,
    "education_score": 85.0,
    "projects_score": 88.0,
    "formatting_score": 90.0,
    "certifications_score": 75.0,
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3", "skill4"],
    "missing_keywords": ["keyword1", "keyword2"],
    "recommended_skills": ["skill5", "skill6"],
    "keywords_match": ["matched keyword 1", "matched keyword 2"]
}}

Score each section 0-100. total_score is weighted average.
Return ONLY valid JSON."""

JD_MATCHING_PROMPT = """You are an expert job-match analyst. Compare the candidate profile against the job description and provide a comprehensive match analysis.

Job Description:
{job_description}

Job Requirements:
{job_requirements}

Required Skills: {required_skills}
Preferred Skills: {preferred_skills}

Candidate Profile:
Name: {candidate_name}
Skills: {candidate_skills}
Total Experience: {candidate_experience} years
Education: {candidate_education}
Projects: {candidate_projects}
Certifications: {candidate_certifications}

Return a valid JSON object:
{{
    "match_score": 82.5,
    "skills_match": {{
        "matched": ["Python", "FastAPI"],
        "missing": ["Kubernetes", "Terraform"],
        "score": 75.0
    }},
    "experience_match": {{
        "required_years": 3,
        "candidate_years": 4,
        "match": true,
        "score": 90.0
    }},
    "education_match": {{
        "required": "Bachelor's in CS",
        "candidate": "Bachelor's in CS",
        "match": true,
        "score": 100.0
    }},
    "projects_match": {{
        "relevant_projects": ["Project 1"],
        "score": 80.0
    }},
    "certifications_match": {{
        "relevant": ["AWS Certified"],
        "score": 85.0
    }},
    "overall_assessment": "Strong candidate with relevant skills and experience",
    "hiring_recommendation": "shortlist",
    "recommendation_reason": "Candidate meets most requirements with strong technical background"
}}

Return ONLY valid JSON."""

INTERVIEW_QUESTIONS_PROMPT = """You are an expert technical interviewer. Generate interview questions tailored to this candidate's profile and the job requirements.

Job Description:
{job_description}

Candidate Profile:
Name: {candidate_name}
Skills: {candidate_skills}
Experience: {candidate_experience} years
Education: {candidate_education}
Projects: {candidate_projects}

Generate exactly 15 interview questions with this distribution:
- 3 HR Questions
- 4 Technical Questions
- 3 Scenario Questions
- 3 Behavioral Questions
- 2 Coding Questions

Return a valid JSON object:
{{
    "questions": [
        {{
            "question": "The interview question text",
            "category": "hr|technical|scenario|behavioral|coding",
            "difficulty": "easy|medium|hard",
            "expected_answer": "Brief description of what a good answer would cover"
        }}
    ]
}}

Questions should be specific to the candidate's skills and the job role.
Return ONLY valid JSON."""

RESUME_SUMMARY_PROMPT = """You are an expert career advisor and resume analyst. Generate a comprehensive professional summary for this candidate.

Candidate Profile:
Name: {candidate_name}
Skills: {candidate_skills}
Experience: {candidate_experience} years
Education: {candidate_education}
Projects: {candidate_projects}
Certifications: {candidate_certifications}
Job Applied For: {job_title}

Return a valid JSON object:
{{
    "summary": "A comprehensive 3-4 sentence professional summary highlighting the candidate's key qualifications, expertise, and value proposition for the role.",
    "strengths": [
        "Strength 1 - specific and evidence-based",
        "Strength 2",
        "Strength 3",
        "Strength 4"
    ],
    "weaknesses": [
        "Weakness 1 - constructive and actionable",
        "Weakness 2"
    ],
    "career_highlights": [
        "Notable achievement 1",
        "Notable achievement 2",
        "Notable achievement 3"
    ],
    "overall_rating": "strong|moderate|weak",
    "fit_for_role": "excellent|good|moderate|poor"
}}

Be specific and reference actual skills and experience from the profile.
Return ONLY valid JSON."""

SKILL_GAP_ANALYSIS_PROMPT = """You are an expert career development advisor. Analyze the skill gaps between the candidate and the job requirements.

Job Description:
{job_description}

Required Skills: {required_skills}
Preferred Skills: {preferred_skills}

Candidate Skills: {candidate_skills}
Candidate Experience: {candidate_experience} years

Return a valid JSON object:
{{
    "matched_skills": [
        {{"skill": "Python", "proficiency": "advanced", "relevance": "high"}},
        {{"skill": "FastAPI", "proficiency": "intermediate", "relevance": "high"}}
    ],
    "missing_skills": [
        {{"skill": "Kubernetes", "importance": "high", "category": "DevOps"}},
        {{"skill": "Terraform", "importance": "medium", "category": "DevOps"}}
    ],
    "recommended_skills": [
        {{"skill": "Docker", "reason": "Essential for modern deployments", "priority": "high"}},
        {{"skill": "CI/CD", "reason": "Important for automation", "priority": "medium"}}
    ],
    "learning_roadmap": [
        {{
            "skill": "Kubernetes",
            "priority": 1,
            "estimated_time": "2-3 months",
            "resources": ["Kubernetes Official Docs", "Udemy Course"],
            "difficulty": "medium"
        }}
    ],
    "overall_skill_match_percentage": 72.5,
    "summary": "Candidate has strong Python backend skills but needs to develop containerization and cloud infrastructure expertise"
}}

Return ONLY valid JSON."""

HIRING_RECOMMENDATION_PROMPT = """You are an expert hiring advisor. Based on all analysis, provide a final hiring recommendation.

Job Title: {job_title}
Job Description: {job_description}

Candidate Name: {candidate_name}
ATS Score: {ats_score}
Match Score: {match_score}
Skills: {candidate_skills}
Experience: {candidate_experience} years

Return a valid JSON object:
{{
    "recommendation": "strong_hire|hire|maybe|reject",
    "confidence": 0.85,
    "reasoning": "Detailed explanation of why this recommendation was made, referencing specific scores, skills, and experience levels.",
    "key_strengths": ["strength1", "strength2", "strength3"],
    "key_concerns": ["concern1", "concern2"],
    "suggested_next_steps": ["Step 1", "Step 2"],
    "risk_level": "low|medium|high",
    "cultural_fit_estimate": "strong|moderate|weak"
}}

Return ONLY valid JSON."""
