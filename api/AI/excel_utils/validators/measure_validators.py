from typing import Dict, Any

def validate_measure_process_capture(data: Dict[str, Any]) -> bool:
    """Validate Process Capture sheet with array structure."""
    if "measureProcessCapture5" not in data:
        raise ValueError("Missing measureProcessCapture5 key")
    
    process_entries = data["measureProcessCapture5"]
    if not isinstance(process_entries, list):
        raise ValueError("measureProcessCapture5 must be an array")
    
    if not process_entries:
        raise ValueError("measureProcessCapture5 array is empty")
    
    required_keys = [
        "measureProcessCapture6", "measureProcessCapture7", "measureProcessCapture8",
        "measureProcessCapture9", "measureProcessCapture10", "measureProcessCapture11",
        "measureProcessCapture12"
    ]

    for i, entry in enumerate(process_entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {i} is not a dict")
        
        for key in required_keys:
            if key not in entry or entry[key] is None:
                entry[key] = ""
            else:
                entry[key] = str(entry[key]).strip()

    all_empty = all(
        not any(entry.get(k) for k in required_keys)
        for entry in process_entries
    )

    if all_empty:
        raise ValueError("No valid process capture data extracted")
    
    return True

def validate_m_prozessparametermodell(data: Dict[str, Any]) -> bool:
    """Validate M-Prozessparametermodell sheet structure with correct frontend schema."""
    
    if "measurePpModel" not in data:
        raise ValueError("Missing measurePpModel key")
    
    pp_model = data["measurePpModel"]
    
    if not isinstance(pp_model, dict):
        raise ValueError("measurePpModel must be a dict")
    
    # Ensure all three arrays exist
    if "measurePpModelY" not in pp_model:
        pp_model["measurePpModelY"] = []
    elif not isinstance(pp_model["measurePpModelY"], list):
        pp_model["measurePpModelY"] = []
    
    if "measurePpModelX" not in pp_model:
        pp_model["measurePpModelX"] = []
    elif not isinstance(pp_model["measurePpModelX"], list):
        pp_model["measurePpModelX"] = []
    
    if "measurePpModelZ" not in pp_model:
        pp_model["measurePpModelZ"] = []
    elif not isinstance(pp_model["measurePpModelZ"], list):
        pp_model["measurePpModelZ"] = []
    
    # Validate output array - should have exactly one object with Y1-Y9 pairs
    if not pp_model["measurePpModelY"]:
        pp_model["measurePpModelY"] = [{}]
    
    if len(pp_model["measurePpModelY"]) > 0:
        output_obj = pp_model["measurePpModelY"][0]
        if not isinstance(output_obj, dict):
            pp_model["measurePpModelY"][0] = {}
            output_obj = pp_model["measurePpModelY"][0]
        
        # Ensure Y1-Y9 fields exist with correct naming convention
        for i in range(1, 10):
            param_key = f"measurePpModelY{i}"
            value_key = f"measurePpModelY{i}Value"
            
            if param_key not in output_obj or output_obj[param_key] is None:
                output_obj[param_key] = ""
            else:
                output_obj[param_key] = str(output_obj[param_key]).strip()
            
            if value_key not in output_obj or output_obj[value_key] is None:
                output_obj[value_key] = ""
            else:
                output_obj[value_key] = str(output_obj[value_key]).strip()
    
    # Validate input array - dynamic X parameters
    # Filter out placeholders and empty entries
    validated_input = []
    for i, input_obj in enumerate(pp_model["measurePpModelX"]):
        if not isinstance(input_obj, dict):
            continue
        
        validated_item = {}
        if "measurePpModelXItem" in input_obj:
            item_value = str(input_obj["measurePpModelXItem"]).strip() if input_obj["measurePpModelXItem"] else ""
            validated_item["measurePpModelXItem"] = item_value
        else:
            validated_item["measurePpModelXItem"] = ""
        
        if "measurePpModelXItemValue" in input_obj:
            validated_item["measurePpModelXItemValue"] = str(input_obj["measurePpModelXItemValue"]).strip() if input_obj["measurePpModelXItemValue"] else ""
        else:
            validated_item["measurePpModelXItemValue"] = ""
        
        # Only include if it has actual content and is not a placeholder
        item_name = validated_item["measurePpModelXItem"]
        if item_name and item_name not in ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10"]:
            validated_input.append(validated_item)
    
    pp_model["measurePpModelX"] = validated_input
    
    # Validate disturbance array - dynamic Z parameters
    # Filter out placeholders and empty entries
    validated_disturbance = []
    for i, dist_obj in enumerate(pp_model["measurePpModelZ"]):
        if not isinstance(dist_obj, dict):
            continue
        
        validated_item = {}
        if "measurePpModelZItem" in dist_obj:
            item_value = str(dist_obj["measurePpModelZItem"]).strip() if dist_obj["measurePpModelZItem"] else ""
            validated_item["measurePpModelZItem"] = item_value
        else:
            validated_item["measurePpModelZItem"] = ""
        
        if "measurePpModelZItemValue" in dist_obj:
            validated_item["measurePpModelZItemValue"] = str(dist_obj["measurePpModelZItemValue"]).strip() if dist_obj["measurePpModelZItemValue"] else ""
        else:
            validated_item["measurePpModelZItemValue"] = ""
        
        # Only include if it has actual content and is not a placeholder
        item_name = validated_item["measurePpModelZItem"]
        if item_name and item_name not in ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "Z9", "Z10"]:
            validated_disturbance.append(validated_item)
    
    pp_model["measurePpModelZ"] = validated_disturbance
    
    # Check if at least some data is provided
    output_has_data = any(
        pp_model["measurePpModelY"][0].get(f"measurePpModelY{i}")
        for i in range(1, 10)
    ) if pp_model["measurePpModelY"] else False
    
    input_has_data = len(pp_model["measurePpModelX"]) > 0
    disturbance_has_data = len(pp_model["measurePpModelZ"]) > 0
    
    if not (output_has_data or input_has_data or disturbance_has_data):
        raise ValueError("No valid process parameter model data extracted")
    
    return True
def validate_m_datenerfassungsplan(data: Dict[str, Any]) -> bool:
    """Validate M-Datenerfassungsplan sheet structure."""
    
    if "measureDataCollectionPlan" not in data:
        raise ValueError("Missing measureDataCollectionPlan key")
    
    plan = data["measureDataCollectionPlan"]
    
    if not isinstance(plan, dict):
        raise ValueError("measureDataCollectionPlan must be a dict")
    
    # Ensure array exists
    if "measureDataCollectionPlan3" not in plan:
        plan["measureDataCollectionPlan3"] = []
    elif not isinstance(plan["measureDataCollectionPlan3"], list):
        plan["measureDataCollectionPlan3"] = []
    
    if not plan["measureDataCollectionPlan3"]:
        raise ValueError("measureDataCollectionPlan3 array is empty")
    
    required_text_fields = [
        "measureDataCollectionPlan5", "measureDataCollectionPlan6", "measureDataCollectionPlan7",
        "measureDataCollectionPlan8", "measureDataCollectionPlan9", "measureDataCollectionPlan13",
        "measureDataCollectionPlan14", "measureDataCollectionPlan15", "measureDataCollectionPlan16",
        "measureDataCollectionPlan19"
    ]
    
    boolean_fields = [
        "measureDataCollectionPlan20", "measureDataCollectionPlan21",
        "measureDataCollectionPlan22", "measureDataCollectionPlan23"
    ]
    
    control_limit_fields = ["measureDataCollectionPlan25", "measureDataCollectionPlan26"]
    
    for i, entry in enumerate(plan["measureDataCollectionPlan3"]):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {i} is not a dict")
        
        # Normalize text fields
        for field in required_text_fields:
            if field not in entry or entry[field] is None:
                entry[field] = ""
            else:
                entry[field] = str(entry[field]).strip()
        
        # Normalize boolean fields
        for field in boolean_fields:
            if field not in entry or entry[field] is None:
                entry[field] = False
            else:
                entry[field] = bool(entry[field])
        
        # Normalize control limit fields (only required if field7 is controlVariable or interferenceVariable)
        field7 = entry.get("measureDataCollectionPlan7", "").lower()
        for field in control_limit_fields:
            if field not in entry or entry[field] is None:
                entry[field] = ""
            else:
                entry[field] = str(entry[field]).strip()
        
        # Validate that field7 has valid value
        valid_types = ["controlvariable", "interferencevariable", "resultvariable"]
        if field7 not in valid_types:
            entry["measureDataCollectionPlan7"] = "resultVariable"
        
        # Validate that field8 has valid value
        field8 = entry.get("measureDataCollectionPlan8", "").lower()
        valid_data_types = ["continuous", "attributiv"]
        if field8 not in valid_data_types:
            entry["measureDataCollectionPlan8"] = "continuous"
    
    # Check if at least some data is provided
    all_empty = all(
        not entry.get("measureDataCollectionPlan5")
        for entry in plan["measureDataCollectionPlan3"]
    )
    
    if all_empty:
        raise ValueError("No valid data collection plan data extracted")
    
    return True

def validate_m_status(data: Dict[str, Any]) -> bool:
    """Validate M-Status sheet structure."""
    
    if "measureStatus" not in data:
        raise ValueError("Missing measureStatus key")
    
    status = data["measureStatus"]
    
    if not isinstance(status, dict):
        raise ValueError("measureStatus must be a dict")
    
    # Define valid values for select fields
    valid_status_values = ["notEvaluated", "onPlan", "risk", "offPlan"]
    valid_correctable_values = ["yes", "no"]
    
    # Status field groups (overall, costs, quality, time, scope, process risk, miscellaneous)
    status_fields = [
        ("measureStatus1", True),  # Overall project status (required)
        ("measureStatus4", False),  # Costs status
        ("measureStatus14", False),  # Quality status
        ("measureStatus24", False),  # Time status
        ("measureStatus34", False),  # Scope status
        ("measureStatus44", False),  # Process risk status
        ("measureStatus54", False),  # Miscellaneous status
    ]
    
    # Correctable fields
    correctable_fields = [
        "measureStatus5", "measureStatus15", "measureStatus25",
        "measureStatus35", "measureStatus45", "measureStatus55"
    ]
    
    # Text/textarea fields
    text_fields = [
        "measureStatus2", "measureStatus6", "measureStatus16",
        "measureStatus26", "measureStatus36", "measureStatus46", "measureStatus56"
    ]
    
    # Validate status fields
    for field, is_required in status_fields:
        if field not in status or status[field] is None:
            if is_required:
                raise ValueError(f"Required field {field} is missing")
            status[field] = "notEvaluated"
        else:
            value = str(status[field]).strip()
            if value.lower() not in [v.lower() for v in valid_status_values]:
                status[field] = "notEvaluated"
            else:
                # Ensure correct casing
                status[field] = next(v for v in valid_status_values if v.lower() == value.lower())
    
    # Validate correctable fields (yes/no)
    for field in correctable_fields:
        if field not in status or status[field] is None:
            status[field] = ""
        else:
            value = str(status[field]).strip().lower()
            if value in ["yes", "no"]:
                status[field] = value
            elif value in ["ja", "j", "true", "1"]:
                status[field] = "yes"
            elif value in ["nein", "n", "false", "0"]:
                status[field] = "no"
            else:
                status[field] = ""
    
    # Validate text fields
    for field in text_fields:
        if field not in status or status[field] is None:
            status[field] = ""
        else:
            status[field] = str(status[field]).strip()
    
    # Validate boolean checkbox field
    if "measureStatus3" not in status or status["measureStatus3"] is None:
        status["measureStatus3"] = False
    else:
        status["measureStatus3"] = bool(status["measureStatus3"])
    
    # Check if at least overall status is provided
    if not status.get("measureStatus1"):
        raise ValueError("No valid status data extracted")
    
    return True

def validate_m_review_protocol(data: Dict[str, Any]) -> bool:
    """Validate M-Review Protokoll sheet structure."""
    
    if "measureReviewProtocol" not in data:
        raise ValueError("Missing measureReviewProtocol key")
    
    protocol = data["measureReviewProtocol"]
    
    if not isinstance(protocol, dict):
        raise ValueError("measureReviewProtocol must be a dict")
    
    # Text fields
    text_fields = [
        "measureReviewProtocol3",  # Projektphase
        "measureReviewProtocol4",  # Teilnehmer
    ]
    
    # Textarea fields
    textarea_fields = [
        "measureReviewProtocol11",  # Inhalte
        "measureReviewProtocol20",  # Sonstiges
        "measureReviewProtocol24",  # Begründung
    ]
    
    # Boolean fields
    boolean_fields = [
        "measureReviewProtocol25",  # Maßnahmen aus vorheriger Phase überprüft
        "measureReviewProtocol22",  # Weiter im Projekt? (Slider)
    ]
    
    # Date field
    date_field = "measureReviewProtocol5"
    
    # Time fields
    time_fields = [
        "measureReviewProtocol6",  # Uhrzeit Start
        "measureReviewProtocol7",  # Uhrzeit End
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
        protocol.get("measureReviewProtocol3"),
        protocol.get("measureReviewProtocol4"),
        protocol.get("measureReviewProtocol5"),
        protocol.get("measureReviewProtocol6"),
        protocol.get("measureReviewProtocol11"),
    ])
    
    if not has_data:
        raise ValueError("No valid review protocol data extracted")
    
    return True

MEASURE_VALIDATORS = {
    "M-Prozesserfassung": validate_measure_process_capture,
    "M-Prozessparametermodell": validate_m_prozessparametermodell,
    "M-Datenerfassungsplan": validate_m_datenerfassungsplan,
    "M-Status": validate_m_status,
    "M-Review Protokoll": validate_m_review_protocol,
}