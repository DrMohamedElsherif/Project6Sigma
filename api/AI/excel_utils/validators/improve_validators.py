from typing import Dict, Any

def validate_i_status(data: Dict[str, Any]) -> bool:
    """Validate I-Status sheet structure."""
    
    if "improveStatus" not in data:
        raise ValueError("Missing improveStatus key")
    
    status = data["improveStatus"]
    
    if not isinstance(status, dict):
        raise ValueError("improveStatus must be a dict")
    
    # Define valid values for select fields
    valid_status_values = ["notEvaluated", "onPlan", "risk", "offPlan"]
    valid_correctable_values = ["yes", "no"]
    
    # Status field groups with their corresponding correctable and comment fields
    status_groups = [
        ("improveReview62", "improveReview63_1", None, True),  # Overall (required)
        ("improveReview66", "improveReview67", "improveReview68", False),  # Cost
        ("improveReview71", "improveReview72", "improveReview73", False),  # Quality
        ("improveReview76", "improveReview77", "improveReview78", False),  # Time
        ("improveReview81", "improveReview82", "improveReview83", False),  # Scope
        ("improveReview86", "improveReview87", "improveReview88", False),  # Process Risk
        ("improveReview91", "improveReview92", "improveReview93", False),  # Miscellaneous
    ]
    
    # Text/textarea fields
    textarea_fields = [
        "improveReview63", "improveReview68", "improveReview73",
        "improveReview78", "improveReview83", "improveReview88", "improveReview93"
    ]
    
    # Normalize overall status field
    if "improveReview62" not in status or status["improveReview62"] is None:
        raise ValueError("Required field improveReview62 is missing")
    else:
        value = str(status["improveReview62"]).strip()
        if value.lower() not in [v.lower() for v in valid_status_values]:
            status["improveReview62"] = "notEvaluated"
        else:
            status["improveReview62"] = next(v for v in valid_status_values if v.lower() == value.lower())
    
    # Normalize boolean checkbox field (improveReview63_1)
    if "improveReview63_1" not in status or status["improveReview63_1"] is None:
        status["improveReview63_1"] = False
    else:
        status["improveReview63_1"] = bool(status["improveReview63_1"])
    
    # Normalize overall summary
    if "improveReview63" not in status or status["improveReview63"] is None:
        status["improveReview63"] = ""
    else:
        status["improveReview63"] = str(status["improveReview63"]).strip()
    
    # Process each status group (skip first which is already processed)
    for status_field, correctable_field, comment_field, _ in status_groups[1:]:
        
        # Validate status field
        if status_field not in status or status[status_field] is None:
            status[status_field] = "notEvaluated"
        else:
            value = str(status[status_field]).strip()
            if value.lower() not in [v.lower() for v in valid_status_values]:
                status[status_field] = "notEvaluated"
            else:
                status[status_field] = next(v for v in valid_status_values if v.lower() == value.lower())
        
        # Validate correctable field (conditional)
        current_status = status.get(status_field, "notEvaluated")
        if correctable_field:
            if current_status in ["risk", "offPlan"]:
                # Field is required/conditional when status is risk or offPlan
                if correctable_field not in status or status[correctable_field] is None:
                    status[correctable_field] = ""
                else:
                    value = str(status[correctable_field]).strip().lower()
                    if value in ["yes", "no"]:
                        status[correctable_field] = value
                    elif value in ["ja", "j", "true", "1"]:
                        status[correctable_field] = "yes"
                    elif value in ["nein", "n", "false", "0"]:
                        status[correctable_field] = "no"
                    else:
                        status[correctable_field] = ""
            else:
                # Field should be empty if status is not risk or offPlan
                status[correctable_field] = ""
        
        # Validate comment field
        if comment_field:
            if comment_field not in status or status[comment_field] is None:
                status[comment_field] = ""
            else:
                status[comment_field] = str(status[comment_field]).strip()
    
    # Check if at least overall status is provided
    if not status.get("improveReview62"):
        raise ValueError("No valid improve status data extracted")
    
    return True

def validate_i_review_protocol(data: Dict[str, Any]) -> bool:
    """Validate I-Review Protokoll sheet structure."""
    
    if "improveReviewProtocol" not in data:
        raise ValueError("Missing improveReviewProtocol key")
    
    protocol = data["improveReviewProtocol"]
    
    if not isinstance(protocol, dict):
        raise ValueError("improveReviewProtocol must be a dict")
    
    # Text fields
    text_fields = [
        "improveReviewProtocol3",  # Projektphase
        "improveReviewProtocol4",  # Teilnehmer
    ]
    
    # Textarea fields
    textarea_fields = [
        "improveReviewProtocol11",  # Inhalte
        "improveReviewProtocol20",  # Sonstiges
        "improveReviewProtocol24",  # Begründung
    ]
    
    # Boolean fields
    boolean_fields = [
        "improveReviewProtocol25",  # Maßnahmen aus vorheriger Phase überprüft
        "improveReviewProtocol22",  # Weiter im Projekt? (Slider)
    ]
    
    # Date field
    date_field = "improveReviewProtocol5"
    
    # Time fields
    time_fields = [
        "improveReviewProtocol6",  # Uhrzeit Start
        "improveReviewProtocol7",  # Uhrzeit End
    ]
    
    # Validate text fields
    for field in text_fields:
        if field not in protocol or protocol[field] is None:
            protocol[field] = ""
        else:
            protocol[field] = str(protocol[field]).strip()
    
    # Validate textarea fields
    for field in textarea_fields:
        if field not in protocol or protocol[field] is None:
            protocol[field] = ""
        else:
            protocol[field] = str(protocol[field]).strip()
    
    # Validate boolean fields
    for field in boolean_fields:
        if field not in protocol or protocol[field] is None:
            protocol[field] = False
        else:
            protocol[field] = bool(protocol[field])
    
    # Validate date field (YYYY-MM-DD format)
    if date_field not in protocol or protocol[date_field] is None:
        protocol[date_field] = ""
    else:
        date_str = str(protocol[date_field]).strip()
        # Basic validation: should be in YYYY-MM-DD format
        if date_str and len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            protocol[date_field] = date_str
        elif date_str:
            # Try to extract date if it's in different format
            protocol[date_field] = date_str
        else:
            protocol[date_field] = ""
    
    # Validate time fields (HH:mm format, 24-hour)
    for field in time_fields:
        if field not in protocol or protocol[field] is None:
            protocol[field] = ""
        else:
            time_str = str(protocol[field]).strip()
            # Basic validation: should be in HH:mm format
            if time_str and len(time_str) == 5 and time_str[2] == ':':
                try:
                    hours = int(time_str[:2])
                    minutes = int(time_str[3:5])
                    if 0 <= hours <= 23 and 0 <= minutes <= 59:
                        protocol[field] = time_str
                    else:
                        protocol[field] = ""
                except ValueError:
                    protocol[field] = ""
            elif time_str:
                # Try to normalize if it's in different format
                protocol[field] = time_str
            else:
                protocol[field] = ""
    
    # Check if at least some data is provided
    has_data = any([
        protocol.get("improveReviewProtocol3"),
        protocol.get("improveReviewProtocol4"),
        protocol.get("improveReviewProtocol5"),
        protocol.get("improveReviewProtocol6"),
        protocol.get("improveReviewProtocol11"),
    ])
    
    if not has_data:
        raise ValueError("No valid review protocol data extracted")
    
    return True


def validate_i_ideenliste(data: Dict[str, Any]) -> bool:
    """Validate I-Ideenliste sheet structure."""
    
    if "improveBrainstorming" not in data:
        raise ValueError("Missing improveBrainstorming key")
    
    brainstorming = data["improveBrainstorming"]
    
    if not isinstance(brainstorming, dict):
        raise ValueError("improveBrainstorming must be a dict")
    
    if "improveBrainstorming1" not in brainstorming:
        raise ValueError("Missing improveBrainstorming1 array")
    
    ideas = brainstorming["improveBrainstorming1"]
    
    if not isinstance(ideas, list):
        raise ValueError("improveBrainstorming1 must be an array")
    
    valid_status_values = ["notEvaluated", "discarded", "followedUp"]
    
    # Validate each idea in the array
    for idx, idea in enumerate(ideas):
        if not isinstance(idea, dict):
            raise ValueError(f"Idea at index {idx} must be a dict")
        
        # Validate improveBrainstorming2 (Idee text)
        if "improveBrainstorming2" not in idea or idea["improveBrainstorming2"] is None:
            idea["improveBrainstorming2"] = ""
        else:
            idea["improveBrainstorming2"] = str(idea["improveBrainstorming2"]).strip()
        
        # Validate improveBrainstorming3 (Bewertung/Status)
        if "improveBrainstorming3" not in idea or idea["improveBrainstorming3"] is None:
            idea["improveBrainstorming3"] = "notEvaluated"
        else:
            value = str(idea["improveBrainstorming3"]).strip()
            if value.lower() not in [v.lower() for v in valid_status_values]:
                idea["improveBrainstorming3"] = "notEvaluated"
            else:
                idea["improveBrainstorming3"] = next(v for v in valid_status_values if v.lower() == value.lower())
        
        # Validate improveBrainstorming6 (Comment - only required when status is "followedUp")
        if "improveBrainstorming6" not in idea or idea["improveBrainstorming6"] is None:
            idea["improveBrainstorming6"] = ""
        else:
            idea["improveBrainstorming6"] = str(idea["improveBrainstorming6"]).strip()
        
        # Clear comment if status is not "followedUp"
        if idea["improveBrainstorming3"] != "followedUp":
            idea["improveBrainstorming6"] = ""
    
    # Check if at least one idea is provided
    if not ideas or not any(idea.get("improveBrainstorming2") for idea in ideas):
        raise ValueError("No valid ideas extracted")
    
    return True

IMPROVE_VALIDATORS = {
    "I-Status": validate_i_status,
    "I-Review Protokoll": validate_i_review_protocol,
    "I-Ideenliste": validate_i_ideenliste,
}