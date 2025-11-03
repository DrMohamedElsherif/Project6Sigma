from typing import Dict, Any

def validate_a_status(data: Dict[str, Any]) -> bool:
    """Validate A-Status sheet structure."""
    
    if "analysisStatus" not in data:
        raise ValueError("Missing analysisStatus key")
    
    status = data["analysisStatus"]
    
    if not isinstance(status, dict):
        raise ValueError("analysisStatus must be a dict")
    
    # Define valid values for select fields
    valid_status_values = ["notEvaluated", "onPlan", "risk", "offPlan"]
    valid_correctable_values = ["yes", "no"]
    
    # Status field groups with their corresponding correctable fields
    status_groups = [
        ("analysisStatus79", "analysisStatus78_1", None, True),  # Overall (required)
        ("analysisStatus83", "analysisStatus84", "analysisStatus85", False),  # Cost
        ("analysisStatus88", "analysisStatus89", "analysisStatus90", False),  # Quality
        ("analysisStatus93", "analysisStatus94", "analysisStatus95", False),  # Time
        ("analysisStatus98", "analysisStatus99", "analysisStatus100", False),  # Scope
        ("analysisStatus103", "analysisStatus104", "analysisStatus105", False),  # Process Risk
        ("analysisStatus108", "analysisStatus109", "analysisStatus110", False),  # Miscellaneous
    ]
    
    # Text/textarea fields
    textarea_fields = [
        "analysisStatus80", "analysisStatus85", "analysisStatus90",
        "analysisStatus95", "analysisStatus100", "analysisStatus105", "analysisStatus110"
    ]
    
    # Normalize overall status field
    if "analysisStatus79" not in status or status["analysisStatus79"] is None:
        raise ValueError("Required field analysisStatus79 is missing")
    else:
        value = str(status["analysisStatus79"]).strip()
        if value.lower() not in [v.lower() for v in valid_status_values]:
            status["analysisStatus79"] = "notEvaluated"
        else:
            status["analysisStatus79"] = next(v for v in valid_status_values if v.lower() == value.lower())
    
    # Normalize boolean checkbox field (analysisStatus78_1)
    if "analysisStatus78_1" not in status or status["analysisStatus78_1"] is None:
        status["analysisStatus78_1"] = False
    else:
        status["analysisStatus78_1"] = bool(status["analysisStatus78_1"])
    
    # Normalize overall summary
    if "analysisStatus80" not in status or status["analysisStatus80"] is None:
        status["analysisStatus80"] = ""
    else:
        status["analysisStatus80"] = str(status["analysisStatus80"]).strip()
    
    # Process each status group
    for i, group in enumerate(status_groups[1:], 1):  # Skip first (already processed)
        status_field, correctable_field, comment_field, _ = group
        
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
    if not status.get("analysisStatus79"):
        raise ValueError("No valid analysis status data extracted")
    
    return True

def validate_a_review_protocol(data: Dict[str, Any]) -> bool:
    """Validate A-Review Protokoll sheet structure."""
    
    if "analysisReviewProtocol" not in data:
        raise ValueError("Missing analysisReviewProtocol key")
    
    protocol = data["analysisReviewProtocol"]
    
    if not isinstance(protocol, dict):
        raise ValueError("analysisReviewProtocol must be a dict")
    
    # Text fields
    text_fields = [
        "analysisReviewProtocol3",  # Projektphase
        "analysisReviewProtocol4",  # Teilnehmer
    ]
    
    # Textarea fields
    textarea_fields = [
        "analysisReviewProtocol11",  # Inhalte
        "analysisReviewProtocol20",  # Sonstiges
        "analysisReviewProtocol24",  # Begründung
    ]
    
    # Boolean fields
    boolean_fields = [
        "analysisReviewProtocol25",  # Maßnahmen aus vorheriger Phase überprüft
        "analysisReviewProtocol22",  # Weiter im Projekt? (Slider)
    ]
    
    # Date field
    date_field = "analysisReviewProtocol5"
    
    # Time fields
    time_fields = [
        "analysisReviewProtocol6",  # Uhrzeit Start
        "analysisReviewProtocol7",  # Uhrzeit End
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
        protocol.get("analysisReviewProtocol3"),
        protocol.get("analysisReviewProtocol4"),
        protocol.get("analysisReviewProtocol5"),
        protocol.get("analysisReviewProtocol6"),
        protocol.get("analysisReviewProtocol11"),
    ])
    
    if not has_data:
        raise ValueError("No valid review protocol data extracted")
    
    return True

ANALYSIS_VALIDATORS = {
    "A-Status": validate_a_status,
    "A-Review Protokoll": validate_a_review_protocol,
}