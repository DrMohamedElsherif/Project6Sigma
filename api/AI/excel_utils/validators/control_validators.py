from typing import Dict, Any

def validate_c_review_lessons_learned(data: Dict[str, Any]) -> bool:
    """Validate C-Review _ Lessons Learned structure."""
    if "controlLessonsLearned1" not in data:
        raise ValueError("Missing controlLessonsLearned1 array")
    
    lessons_list = data["controlLessonsLearned1"]
    
    if not isinstance(lessons_list, list):
        raise ValueError("controlLessonsLearned1 must be a list")
    
    if not lessons_list:
        raise ValueError("controlLessonsLearned1 array cannot be empty")
    
    valid_perspective_values = ["innerPerspektive", "outerPerspektive"]
    
    # Validate each lesson learned row
    for idx, row in enumerate(lessons_list):
        if not isinstance(row, dict):
            raise ValueError(f"Lesson learned row {idx} must be an object")
        
        # Validate controlLessonsLearned2 (Perspective select field)
        if "controlLessonsLearned2" not in row or row["controlLessonsLearned2"] is None:
            row["controlLessonsLearned2"] = ""
        else:
            value = str(row["controlLessonsLearned2"]).strip()
            if value not in valid_perspective_values:
                row["controlLessonsLearned2"] = ""
            else:
                row["controlLessonsLearned2"] = value
        
        # Validate boolean fields (checkboxes)
        for bfield in ("controlLessonsLearned3", "controlLessonsLearned4", "controlLessonsLearned5", "controlLessonsLearned6"):
            if bfield not in row or row[bfield] is None:
                row[bfield] = False
            else:
                row[bfield] = bool(row[bfield])
        
        # Validate text fields (comments and recommendations)
        for tfield in ("controlLessonsLearned7", "controlLessonsLearned8"):
            if tfield not in row or row[tfield] is None:
                row[tfield] = ""
            else:
                row[tfield] = str(row[tfield]).strip()
    
    # Check if at least one row has meaningful data
    found_data = False
    for row in lessons_list:
        if row.get("controlLessonsLearned2") or row.get("controlLessonsLearned7") or row.get("controlLessonsLearned8"):
            found_data = True
            break
    
    if not found_data:
        raise ValueError("No valid lesson learned data extracted")
    
    return True

def validate_c_status(data: Dict[str, Any]) -> bool:
    """Validate C-Status sheet structure."""
    
    if "controlStatus" not in data:
        raise ValueError("Missing controlStatus key")
    
    status = data["controlStatus"]
    
    if not isinstance(status, dict):
        raise ValueError("controlStatus must be a dict")
    
    # Define valid values for select fields
    valid_status_values = ["notEvaluated", "onPlan", "risk", "offPlan"]
    valid_correctable_values = ["yes", "no"]
    
    # Status field groups with their corresponding correctable and comment fields
    status_groups = [
        ("controlReview55", "controlReview57", None, True),  # Overall (required)
        ("controlReview60", "controlReview61", "controlReview62", False),  # Cost
        ("controlReview65", "controlReview66", "controlReview67", False),  # Quality
        ("controlReview70", "controlReview71", "controlReview72", False),  # Time
        ("controlReview75", "controlReview76", "controlReview77", False),  # Scope
        ("controlReview80", "controlReview81", "controlReview82", False),  # Process Risk
        ("controlReview85", "controlReview86", "controlReview87", False),  # Miscellaneous
    ]
    
    # Text/textarea fields
    textarea_fields = [
        "controlReview56", "controlReview62", "controlReview67",
        "controlReview72", "controlReview77", "controlReview82", "controlReview87"
    ]
    
    # Normalize overall status field
    if "controlReview55" not in status or status["controlReview55"] is None:
        raise ValueError("Required field controlReview55 is missing")
    else:
        value = str(status["controlReview55"]).strip()
        if value.lower() not in [v.lower() for v in valid_status_values]:
            status["controlReview55"] = "notEvaluated"
        else:
            status["controlReview55"] = next(v for v in valid_status_values if v.lower() == value.lower())
    
    # Normalize boolean checkbox field (controlReview57)
    if "controlReview57" not in status or status["controlReview57"] is None:
        status["controlReview57"] = False
    else:
        status["controlReview57"] = bool(status["controlReview57"])
    
    # Normalize overall summary
    if "controlReview56" not in status or status["controlReview56"] is None:
        status["controlReview56"] = ""
    else:
        status["controlReview56"] = str(status["controlReview56"]).strip()
    
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
    if not status.get("controlReview55"):
        raise ValueError("No valid control status data extracted")
    
    return True

def validate_c_review_protocol(data: Dict[str, Any]) -> bool:
    """Validate C-Review Protokoll sheet structure."""
    
    if "controlReviewProtocol" not in data:
        raise ValueError("Missing controlReviewProtocol key")
    
    protocol = data["controlReviewProtocol"]
    
    if not isinstance(protocol, dict):
        raise ValueError("controlReviewProtocol must be a dict")
    
    # Text fields
    text_fields = [
        "controlReviewProtocol3",  # Projektphase
        "controlReviewProtocol4",  # Teilnehmer
    ]
    
    # Textarea fields
    textarea_fields = [
        "controlReviewProtocol11",  # Inhalte
        "controlReviewProtocol20",  # Sonstiges
        "controlReviewProtocol24",  # Begründung
    ]
    
    # Boolean fields
    boolean_fields = [
        "measureReviewProtocol25",  # Maßnahmen aus vorheriger Phase überprüft
        "controlReviewProtocol22",  # Weiter im Projekt? (Slider)
    ]
    
    # Date field
    date_field = "controlReviewProtocol5"
    
    # Time fields
    time_fields = [
        "controlReviewProtocol6",  # Uhrzeit Start
        "controlReviewProtocol7",  # Uhrzeit End
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
        protocol.get("controlReviewProtocol3"),
        protocol.get("controlReviewProtocol4"),
        protocol.get("controlReviewProtocol5"),
        protocol.get("controlReviewProtocol6"),
        protocol.get("controlReviewProtocol11"),
    ])
    
    if not has_data:
        raise ValueError("No valid review protocol data extracted")
    
    return True

CONTROL_VALIDATORS = {
    "C-Review _ Lessons Learned": validate_c_review_lessons_learned,
    "C-Status": validate_c_status,
    "C-Review Protokoll": validate_c_review_protocol,
}