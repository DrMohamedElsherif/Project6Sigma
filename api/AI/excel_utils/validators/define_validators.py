from typing import Dict, Any

def validate_d_voc_to_ctx(data: Dict[str, Any]) -> bool:
    """Validate D-VoC to CTx sheet with array structure."""    
    if "defineVoc2" not in data:
        raise ValueError("Missing defineVoc2 key")
    
    voc_entries = data["defineVoc2"]
    if not isinstance(voc_entries, list):
        raise ValueError("defineVoc2 must be an array")
    
    if not voc_entries:
        raise ValueError("defineVoc2 array is empty")
    
    for i, entry in enumerate(voc_entries):        
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {i} is not a dict")
        
        for text_key in ("defineVoc7", "defineVoc8", "defineVoc9", "defineVoc10", "defineVoc11"):
            if text_key in entry and entry[text_key] is not None:
                entry[text_key] = str(entry[text_key]).strip()
    
    all_empty = all(
        entry.get("defineVoc3", 0) == 0 and
        not any(entry.get(k) for k in ["defineVoc4", "defineVoc5", "defineVoc6"]) and
        not any(entry.get(k) for k in ["defineVoc7", "defineVoc8", "defineVoc9", "defineVoc10", "defineVoc11"])
        for entry in voc_entries
    )
    
    if all_empty:
        raise ValueError("No valid VOC data extracted")
    
    return True

def validate_d_sipoc(data: Dict[str, Any]) -> bool:
    """Validate D_SIPOC sheet with nested structure."""    
    if "defineSipoc" not in data:
        raise ValueError("Missing defineSipoc key")
    
    sipoc_data = data["defineSipoc"]
    
    required_keys = {
        "defineSipoc6": "",
        "defineSipoc8": [],
        "defineSipoc10": "",
        "defineSipoc12": [],
        "defineSipoc19": [],
        "defineSipoc26": [],
        "defineSipoc31": ""
    }
    
    for key, default_value in required_keys.items():
        if key not in sipoc_data:
            sipoc_data[key] = default_value
    
    # Validate arrays
    for key in ["defineSipoc8", "defineSipoc12", "defineSipoc19", "defineSipoc26"]:
        if not isinstance(sipoc_data[key], list):
            sipoc_data[key] = []
        if len(sipoc_data[key]) == 0:
            if key == "defineSipoc8":
                sipoc_data[key] = [{"defineSipoc9": ""}]
            elif key == "defineSipoc12":
                sipoc_data[key] = [{"defineSipoc14": "", "defineSipoc16": [{"defineSipoc17": ""}]}]
            elif key == "defineSipoc19":
                sipoc_data[key] = [{"defineSipoc21": "", "defineSipoc23": [{"defineSipoc24": ""}]}]
            else:
                sipoc_data[key] = [{"defineSipoc28": "", "defineSipoc30": ""}]
    
    all_empty = (
        not sipoc_data["defineSipoc6"] and
        not sipoc_data["defineSipoc10"] and
        not sipoc_data["defineSipoc31"] and
        all(not item.get("defineSipoc9") for item in sipoc_data["defineSipoc8"]) and
        all(not output.get("defineSipoc14") for output in sipoc_data["defineSipoc12"]) and
        all(not input_item.get("defineSipoc21") for input_item in sipoc_data["defineSipoc19"]) and
        all(not kpi.get("defineSipoc28") for kpi in sipoc_data["defineSipoc26"])
    )
    
    if all_empty:
        raise ValueError("No valid SIPOC data extracted")
    
    return True

def validate_info_sammlung(data: Dict[str, Any]) -> bool:
    """Validate Info-Sammlung sheet with array structure."""
    if "defineFacts4" not in data:
        raise ValueError("Missing defineFacts4 key")
    
    facts_entries = data["defineFacts4"]
    if not isinstance(facts_entries, list):
        raise ValueError("defineFacts4 must be an array")
    
    if not facts_entries:
        raise ValueError("defineFacts4 array is empty")
    
    # Validate date format if present
    if "defineFacts2" in data and data["defineFacts2"]:
        date_str = str(data["defineFacts2"]).strip()
        if not is_valid_iso_date(date_str):
            raise ValueError("defineFacts2 must be in ISO format YYYY-MM-DD")
    else:
        data["defineFacts2"] = ""
    
    for i, entry in enumerate(facts_entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {i} is not a dict")
        
        # Validate defineFacts6 (Information)
        if "defineFacts6" not in entry or not entry["defineFacts6"]:
            raise ValueError(f"Entry {i}: defineFacts6 (Information) is required")
        entry["defineFacts6"] = str(entry["defineFacts6"]).strip()
        
        # Validate defineFacts7 (Type: fact or hypothesis)
        if "defineFacts7" not in entry or entry["defineFacts7"] not in ["fact", "hypothesis"]:
            raise ValueError(f"Entry {i}: defineFacts7 must be 'fact' or 'hypothesis'")
        
        # Validate boolean fields
        for bool_key in ["defineFacts9", "defineFacts10", "defineFacts11"]:
            if bool_key not in entry or entry[bool_key] is None:
                entry[bool_key] = False
            else:
                entry[bool_key] = bool(entry[bool_key])
        
        # Validate text fields
        for text_key in ["defineFacts12", "defineFacts13"]:
            if text_key not in entry or entry[text_key] is None:
                entry[text_key] = ""
            else:
                entry[text_key] = str(entry[text_key]).strip()
    
    # Ensure overall comment field exists
    if "defineFacts13" not in data:
        data["defineFacts13"] = ""
    else:
        data["defineFacts13"] = str(data["defineFacts13"]).strip()
    
    return True

def is_valid_iso_date(date_str: str) -> bool:
    """Check if date string is in ISO format YYYY-MM-DD."""
    import re
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_str))

def validate_define_problem(data: Dict[str, Any]) -> bool:
    """Validate Define Problem sheet structure."""
    if "defineProblem" not in data:
        raise ValueError("Missing defineProblem key")
    
    problem_data = data["defineProblem"]
    
    required_keys = {
        "defineProblem1": "",
        "defineProblem2": "",
        "defineProblem3": "",
        "defineProblem4": "",
        "defineProblem5": "",
        "defineProblem6": "",
        "defineProblem7": "",
        "defineProblem8": "",
        "defineProblem9": "",
        "defineProblem10": "",
        "defineProblem11": "",
        "defineProblem12": ""
    }
    
    # Ensure all required keys exist
    for key, default_value in required_keys.items():
        if key not in problem_data:
            problem_data[key] = default_value
        else:
            problem_data[key] = str(problem_data[key]).strip() if problem_data[key] else ""
    
    # Validate defineProblem11 - must be one of the predefined values
    valid_error_patterns = ["konstant", "zyklisch", "stetig fallend", "zufällig", "sporadisch"]
    if problem_data["defineProblem11"] and problem_data["defineProblem11"] not in valid_error_patterns:
        raise ValueError(f"defineProblem11 must be one of: {', '.join(valid_error_patterns)}")
    
    # Check if at least some problem data is provided
    all_empty = all(
        not problem_data.get(key)
        for key in ["defineProblem1", "defineProblem2", "defineProblem5", "defineProblem8"]
    )
    
    if all_empty:
        raise ValueError("No valid problem definition data extracted")
    
    return True

def validate_d_status(data: Dict[str, Any]) -> bool:
    """Validate D-Status sheet structure."""
    
    valid_statuses = ["onPlan", "offPlan", "risk", "notEvaluated"]
    valid_correctable = ["yes", "no"]
    
    # Define sections: (status_field, correctable_field, comment_field)
    sections = [
        ("defineStatus1", "defineStatus4", "defineStatus5"),
        ("defineStatus12", "defineStatus13", "defineStatus14"),
        ("defineStatus21", "defineStatus22", "defineStatus23"),
        ("defineStatus31", "defineStatus32", "defineStatus33"),
        ("defineStatus41", "defineStatus42", "defineStatus43"),
        ("defineStatus51", "defineStatus52", "defineStatus53"),
    ]
    
    # Ensure defineStatus2 (summary) exists
    if "defineStatus2" not in data:
        data["defineStatus2"] = ""
    else:
        data["defineStatus2"] = str(data["defineStatus2"]).strip() if data["defineStatus2"] else ""
    
    for status_field, correctable_field, comment_field in sections:
        # Ensure status field exists and is valid
        if status_field not in data or not data[status_field]:
            data[status_field] = "notEvaluated"
        else:
            status_value = str(data[status_field]).strip()
            if status_value not in valid_statuses:
                raise ValueError(f"{status_field} must be one of: {', '.join(valid_statuses)}")
            data[status_field] = status_value
        
        # Ensure correctable field follows the conditional logic
        if correctable_field not in data:
            data[correctable_field] = ""
        else:
            data[correctable_field] = str(data[correctable_field]).strip() if data[correctable_field] else ""
        
        # Validate correctable field: only should have value if status is "risk" or "offPlan"
        if data[status_field] in ["risk", "offPlan"]:
            if data[correctable_field] and data[correctable_field] not in valid_correctable:
                raise ValueError(f"{correctable_field} must be 'yes' or 'no' when {status_field} is 'risk' or 'offPlan'")
        else:
            # If status is not "risk" or "offPlan", correctable field should be empty
            data[correctable_field] = ""
        
        # Ensure comment field exists
        if comment_field not in data:
            data[comment_field] = ""
        else:
            data[comment_field] = str(data[comment_field]).strip() if data[comment_field] else ""
    
    # Check if at least some status data is provided
    all_empty = all(
        data.get(status_field) == "notEvaluated"
        for status_field, _, _ in sections
    )
    
    if all_empty:
        raise ValueError("No valid status data extracted")
    
    return True

def validate_d_review_protokoll(data: Dict[str, Any]) -> bool:
    """Validate D-Review Protokoll sheet structure."""
    
    required_keys = {
        "defineReviewProtocol3": "",
        "defineReviewProtocol4": "",
        "defineReviewProtocol5": "",
        "defineReviewProtocol6": "",
        "defineReviewProtocol7": "",
        "defineReviewProtocol11": "",
        "defineReviewProtocol20": "",
        "defineReviewProtocol22": False,
        "defineReviewProtocol24": ""
    }
    
    # Ensure all required keys exist
    for key, default_value in required_keys.items():
        if key not in data:
            data[key] = default_value
    
    # Validate date format
    if data["defineReviewProtocol5"] and data["defineReviewProtocol5"] != "":
        date_str = str(data["defineReviewProtocol5"]).strip()
        if not is_valid_iso_date(date_str):
            raise ValueError("defineReviewProtocol5 must be in ISO format YYYY-MM-DD")
    else:
        data["defineReviewProtocol5"] = ""
    
    # Validate time formats
    for time_field in ["defineReviewProtocol6", "defineReviewProtocol7"]:
        if data[time_field] and data[time_field] != "":
            time_str = str(data[time_field]).strip()
            if not is_valid_time(time_str):
                raise ValueError(f"{time_field} must be in HH:MM format")
        else:
            data[time_field] = ""
    
    # Validate boolean field
    if "defineReviewProtocol22" in data and data["defineReviewProtocol22"] is not None:
        data["defineReviewProtocol22"] = bool(data["defineReviewProtocol22"])
    else:
        data["defineReviewProtocol22"] = False
    
    # Validate text fields
    for text_field in ["defineReviewProtocol3", "defineReviewProtocol4", "defineReviewProtocol11", "defineReviewProtocol20", "defineReviewProtocol24"]:
        if text_field not in data or data[text_field] is None:
            data[text_field] = ""
        else:
            data[text_field] = str(data[text_field]).strip()
    
    # Conditional validation: defineReviewProtocol24 is required if defineReviewProtocol22 is false
    if not data["defineReviewProtocol22"] and not data["defineReviewProtocol24"]:
        raise ValueError("defineReviewProtocol24 (Reason for not continuing) is required when defineReviewProtocol22 is false")
    
    # Check if at least some protocol data is provided
    all_empty = all(
        not data.get(key) or key == "defineReviewProtocol22"
        for key in ["defineReviewProtocol3", "defineReviewProtocol5", "defineReviewProtocol11"]
    )
    
    if all_empty:
        raise ValueError("No valid review protocol data extracted")
    
    return True

def is_valid_time(time_str: str) -> bool:
    """Check if time string is in HH:MM format."""
    import re
    return bool(re.match(r'^\d{2}:\d{2}$', time_str))

def validate_d_stakeholderanalysis(data: Dict[str, Any]) -> bool:
    """Validate D-Stakeholderanalysis sheet with correct schema structure."""
    
    if "defineSteakholder4" not in data:
        raise ValueError("Missing defineSteakholder4 key")
    
    stakeholders = data["defineSteakholder4"]
    if not isinstance(stakeholders, list):
        raise ValueError("defineSteakholder4 must be an array")
    
    # Allow empty arrays - this might be valid for some sheets
    if not stakeholders:
        print("[DEBUG] Warning: defineSteakholder4 array is empty - this might be valid if no stakeholders exist")
        return True
    
    valid_levels = [1, 2, 3]  # 1=hoch, 2=mittel, 3=gering
    valid_characters = [0, 1, 2]  # 0=not set, 1=proaktiv, 2=reaktiv
    valid_categories = [0, 1, 2]  # 0=not set, 1=positives stärken, 2=negatives abwenden
    
    for i, stakeholder in enumerate(stakeholders):
        if not isinstance(stakeholder, dict):
            raise ValueError(f"Entry {i} is not a dict")
        
        # Validate text fields
        for text_key in ["defineSteakholder6", "defineSteakholder7", "defineSteakholder8", "defineSteakholder9", "defineSteakholder10"]:
            if text_key not in stakeholder or stakeholder[text_key] is None:
                stakeholder[text_key] = ""
            else:
                stakeholder[text_key] = str(stakeholder[text_key]).strip()
        
        # Validate required name field
        if not stakeholder["defineSteakholder6"]:
            raise ValueError(f"Entry {i}: defineSteakholder6 (Name) is required")
        
        # Validate level fields (must be one of the numeric values)
        for level_key in ["defineSteakholder12", "defineSteakholder13", "defineSteakholder14", "defineSteakholder15", "defineSteakholder16"]:
            if level_key not in stakeholder or stakeholder[level_key] is None:
                stakeholder[level_key] = 3  # Default to gering
            else:
                try:
                    level_value = int(stakeholder[level_key])
                    if level_value not in valid_levels:
                        raise ValueError(f"Entry {i}: {level_key} must be one of: {valid_levels}")
                    stakeholder[level_key] = level_value
                except (ValueError, TypeError):
                    raise ValueError(f"Entry {i}: {level_key} must be a numeric value (1, 2, or 3)")
        
        # Validate measures array
        if "defineSteakholder18" not in stakeholder:
            stakeholder["defineSteakholder18"] = []
        elif not isinstance(stakeholder["defineSteakholder18"], list):
            stakeholder["defineSteakholder18"] = []
        
        measures = stakeholder["defineSteakholder18"]
        for j, measure in enumerate(measures):
            if not isinstance(measure, dict):
                raise ValueError(f"Entry {i}, Measure {j}: is not a dict")
            
            # Validate measure text fields
            for measure_text_key in ["defineSteakholder19", "defineSteakholder20"]:
                if measure_text_key not in measure or measure[measure_text_key] is None:
                    measure[measure_text_key] = ""
                else:
                    measure[measure_text_key] = str(measure[measure_text_key]).strip()
            
            # Validate measure character field (defineSteakholder21)
            if "defineSteakholder21" not in measure or measure["defineSteakholder21"] is None:
                measure["defineSteakholder21"] = 0  # Default to not set
            else:
                try:
                    character_value = int(measure["defineSteakholder21"])
                    if character_value not in valid_characters:
                        # Set to 0 if invalid value
                        measure["defineSteakholder21"] = 0
                    else:
                        measure["defineSteakholder21"] = character_value
                except (ValueError, TypeError):
                    measure["defineSteakholder21"] = 0
            
            # Validate measure category field (defineSteakholder22)
            if "defineSteakholder22" not in measure or measure["defineSteakholder22"] is None:
                measure["defineSteakholder22"] = 0  # Default to not set
            else:
                try:
                    category_value = int(measure["defineSteakholder22"])
                    if category_value not in valid_categories:
                        # Set to 0 if invalid value
                        measure["defineSteakholder22"] = 0
                    else:
                        measure["defineSteakholder22"] = category_value
                except (ValueError, TypeError):
                    measure["defineSteakholder22"] = 0
    
    return True


DEFINE_VALIDATORS = {
    "D-VoC to CTx": validate_d_voc_to_ctx,
    "D-SIPOC": validate_d_sipoc,
    "Info-Sammlung": validate_info_sammlung,
    "D-Problembeschreibung": validate_define_problem,
    "D-Status": validate_d_status,
    "D-Review Protokoll": validate_d_review_protokoll,
    "D-Stakeholderanalysis": validate_d_stakeholderanalysis,
}
