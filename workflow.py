from IDXClient import IDXClient


def reset(idx_client: IDXClient) -> None:
    """Reset the IDXClient instance to its initial state."""
    idx_client.settings_page.logout()
    idx_client.login_page.login()
    idx_client.settings_page.change_group(2)
    idx_client.vtb_page.select_vtb_option("Patient Services")


def process_invoice(idx_client: IDXClient,invoice_number: str, group_number: str | None) -> None:  
    """Process an invoice using the provided IDXClient instance."""  
    
    if 'P' in invoice_number:
        invoice_number = str(invoice_number[1:])
    else:
        invoice_number = str(invoice_number)
        
    if not group_number or group_number.strip() == "":
        group_number = '3'
    
    # Navigate to patient inquiry
    idx_client.patient_services.navigate_to_patient_inquiry(invoice_number, group_number)
    
    # Navigate to demand statement
    idx_client.patient_services.invoice_list.navigate_to_demand_statement()
    idx_client.patient_services.demand_statement.demand_statement()
    
    # Search for invoice
    idx_client.patient_services.select_invoices.search_for_invoice(invoice_number)
    
    # select device and save output if printed to new screen
    idx_client.patient_services.device_selection.select_device()
    idx_client.vtb_page.select_vtb_option("Patient Services")
    # idx_client.vtb_page._handle_deceased_indicator()