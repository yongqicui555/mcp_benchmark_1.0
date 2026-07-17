def data_report_generator(data, report_title="Data Report", format_type="text", include_summary=True, include_percentages=False, sort_by_value=False):
    """
    Generate readable text reports from dictionary data with various formatting options.
    
    Args:
        data: Dictionary containing data to report (e.g., {'sales': 5000, 'expenses': 3000})
        report_title: Title for the report (default: "Data Report")
        format_type: Output format - "text", "markdown", "html_simple" (default: "text")
        include_summary: Include a summary section with totals and calculations (default: True)
        include_percentages: Calculate and include percentages (default: False)
        sort_by_value: Sort items by value instead of key (default: False)
    
    Returns:
        Dictionary containing the formatted report and metadata
    """
    import json
    from datetime import datetime
    
    def format_currency(value):
        """Format numbers as currency"""
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    def format_number(value):
        """Format numbers with commas"""
        try:
            return f"{float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    def calculate_percentages(data_dict, total_key=None):
        """Calculate percentages for dictionary values"""
        if not data_dict:
            return {}
        
        # If total_key is provided, use that value as total
        if total_key and total_key in data_dict:
            total = float(data_dict[total_key])
        else:
            # Otherwise sum all values
            total = sum(float(v) for v in data_dict.values() if isinstance(v, (int, float)))
        
        if total == 0:
            return {k: 0.0 for k in data_dict.keys()}
        
        percentages = {}
        for key, value in data_dict.items():
            try:
                if isinstance(value, (int, float)):
                    percentages[key] = (float(value) / total) * 100
                else:
                    percentages[key] = 0.0
            except (ValueError, TypeError):
                percentages[key] = 0.0
        
        return percentages
    
    def generate_text_report(data_dict, title, show_summary, show_percentages, sort_values):
        """Generate plain text report"""
        report_lines = []
        
        # Header
        report_lines.append("=" * 60)
        report_lines.append(f"{title.upper()}")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Sort data
        if sort_values:
            sorted_items = sorted(data_dict.items(), key=lambda x: float(x[1]) if isinstance(x[1], (int, float)) else 0, reverse=True)
        else:
            sorted_items = sorted(data_dict.items())
        
        # Data section
        report_lines.append("DATA:")
        report_lines.append("-" * 40)
        
        max_key_length = max(len(str(k)) for k in data_dict.keys())
        
        for key, value in sorted_items:
            if isinstance(value, (int, float)):
                formatted_value = format_currency(value)
            else:
                formatted_value = str(value)
            
            line = f"{key:<{max_key_length}} : {formatted_value:>15}"
            report_lines.append(line)
        
        report_lines.append("")
        
        # Percentages section
        if show_percentages:
            percentages = calculate_percentages(data_dict)
            if percentages:
                report_lines.append("PERCENTAGES:")
                report_lines.append("-" * 40)
                
                for key, value in sorted_items:
                    if key in percentages:
                        pct = percentages[key]
                        line = f"{key:<{max_key_length}} : {pct:>14.1f}%"
                        report_lines.append(line)
                
                report_lines.append("")
        
        # Summary section
        if show_summary:
            report_lines.append("SUMMARY:")
            report_lines.append("-" * 40)
            
            # Calculate totals for numeric values
            numeric_values = [float(v) for v in data_dict.values() if isinstance(v, (int, float))]
            if numeric_values:
                total = sum(numeric_values)
                count = len(numeric_values)
                avg = total / count if count > 0 else 0
                min_val = min(numeric_values) if numeric_values else 0
                max_val = max(numeric_values) if numeric_values else 0
                
                report_lines.append(f"Total items: {len(data_dict)}")
                report_lines.append(f"Numeric items: {count}")
                report_lines.append(f"Total value: {format_currency(total)}")
                report_lines.append(f"Average value: {format_currency(avg)}")
                report_lines.append(f"Minimum value: {format_currency(min_val)}")
                report_lines.append(f"Maximum value: {format_currency(max_val)}")
                
                # Additional calculations for financial data
                financial_keys = ['sales', 'revenue', 'income', 'expenses', 'costs', 'profit', 'loss']
                found_keys = [k for k in data_dict.keys() if any(financial in str(k).lower() for financial in financial_keys)]
                
                if found_keys:
                    report_lines.append("")
                    report_lines.append("Financial Analysis:")
                    
                    # Try to identify sales/revenue and expenses
                    revenue_keys = [k for k in found_keys if any(word in str(k).lower() for word in ['sales', 'revenue', 'income'])]
                    expense_keys = [k for k in found_keys if any(word in str(k).lower() for word in ['expenses', 'costs'])]
                    profit_keys = [k for k in found_keys if any(word in str(k).lower() for word in ['profit', 'loss'])]
                    
                    if revenue_keys and expense_keys:
                        total_revenue = sum(float(data_dict[k]) for k in revenue_keys if isinstance(data_dict[k], (int, float)))
                        total_expenses = sum(float(data_dict[k]) for k in expense_keys if isinstance(data_dict[k], (int, float)))
                        
                        if total_revenue > 0:
                            expense_ratio = (total_expenses / total_revenue) * 100
                            report_lines.append(f"Expense to Revenue Ratio: {expense_ratio:.1f}%")
            
            report_lines.append("")
        
        # Footer
        report_lines.append("=" * 60)
        report_lines.append("End of Report")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def generate_markdown_report(data_dict, title, show_summary, show_percentages, sort_values):
        """Generate markdown report"""
        report_lines = []
        
        # Header
        report_lines.append(f"# {title}")
        report_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        report_lines.append("")
        
        # Sort data
        if sort_values:
            sorted_items = sorted(data_dict.items(), key=lambda x: float(x[1]) if isinstance(x[1], (int, float)) else 0, reverse=True)
        else:
            sorted_items = sorted(data_dict.items())
        
        # Data section
        report_lines.append("## Data")
        report_lines.append("")
        report_lines.append("| Item | Value |")
        report_lines.append("|------|-------|")
        
        for key, value in sorted_items:
            if isinstance(value, (int, float)):
                formatted_value = format_currency(value)
            else:
                formatted_value = str(value)
            
            report_lines.append(f"| {key} | {formatted_value} |")
        
        report_lines.append("")
        
        # Percentages section
        if show_percentages:
            percentages = calculate_percentages(data_dict)
            if percentages:
                report_lines.append("## Percentages")
                report_lines.append("")
                report_lines.append("| Item | Percentage |")
                report_lines.append("|------|------------|")
                
                for key, value in sorted_items:
                    if key in percentages:
                        pct = percentages[key]
                        report_lines.append(f"| {key} | {pct:.1f}% |")
                
                report_lines.append("")
        
        # Summary section
        if show_summary:
            report_lines.append("## Summary")
            report_lines.append("")
            
            # Calculate totals for numeric values
            numeric_values = [float(v) for v in data_dict.values() if isinstance(v, (int, float))]
            if numeric_values:
                total = sum(numeric_values)
                count = len(numeric_values)
                avg = total / count if count > 0 else 0
                min_val = min(numeric_values) if numeric_values else 0
                max_val = max(numeric_values) if numeric_values else 0
                
                report_lines.append(f"- **Total items:** {len(data_dict)}")
                report_lines.append(f"- **Numeric items:** {count}")
                report_lines.append(f"- **Total value:** {format_currency(total)}")
                report_lines.append(f"- **Average value:** {format_currency(avg)}")
                report_lines.append(f"- **Minimum value:** {format_currency(min_val)}")
                report_lines.append(f"- **Maximum value:** {format_currency(max_val)}")
        
        return "\n".join(report_lines)
    
    def generate_html_simple_report(data_dict, title, show_summary, show_percentages, sort_values):
        """Generate simple HTML report"""
        html_lines = []
        
        # HTML header
        html_lines.append("<!DOCTYPE html>")
        html_lines.append("<html>")
        html_lines.append("<head>")
        html_lines.append(f"<title>{title}</title>")
        html_lines.append("<style>")
        html_lines.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html_lines.append("h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }")
        html_lines.append("h2 { color: #555; margin-top: 20px; }")
        html_lines.append("table { border-collapse: collapse; width: 100%; margin: 20px 0; }")
        html_lines.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html_lines.append("th { background-color: #f2f2f2; }")
        html_lines.append("tr:nth-child(even) { background-color: #f9f9f9; }")
        html_lines.append(".footer { margin-top: 30px; color: #777; font-size: 0.9em; }")
        html_lines.append("</style>")
        html_lines.append("</head>")
        html_lines.append("<body>")
        
        # Header
        html_lines.append(f"<h1>{title}</h1>")
        html_lines.append(f"<p><em>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>")
        
        # Sort data
        if sort_values:
            sorted_items = sorted(data_dict.items(), key=lambda x: float(x[1]) if isinstance(x[1], (int, float)) else 0, reverse=True)
        else:
            sorted_items = sorted(data_dict.items())
        
        # Data section
        html_lines.append("<h2>Data</h2>")
        html_lines.append("<table>")
        html_lines.append("<tr><th>Item</th><th>Value</th></tr>")
        
        for key, value in sorted_items:
            if isinstance(value, (int, float)):
                formatted_value = format_currency(value)
            else:
                formatted_value = str(value)
            
            html_lines.append(f"<tr><td>{key}</td><td>{formatted_value}</td></tr>")
        
        html_lines.append("</table>")
        
        # Percentages section
        if show_percentages:
            percentages = calculate_percentages(data_dict)
            if percentages:
                html_lines.append("<h2>Percentages</h2>")
                html_lines.append("<table>")
                html_lines.append("<tr><th>Item</th><th>Percentage</th></tr>")
                
                for key, value in sorted_items:
                    if key in percentages:
                        pct = percentages[key]
                        html_lines.append(f"<tr><td>{key}</td><td>{pct:.1f}%</td></tr>")
                
                html_lines.append("</table>")
        
        # Summary section
        if show_summary:
            html_lines.append("<h2>Summary</h2>")
            
            # Calculate totals for numeric values
            numeric_values = [float(v) for v in data_dict.values() if isinstance(v, (int, float))]
            if numeric_values:
                total = sum(numeric_values)
                count = len(numeric_values)
                avg = total / count if count > 0 else 0
                min_val = min(numeric_values) if numeric_values else 0
                max_val = max(numeric_values) if numeric_values else 0
                
                html_lines.append("<ul>")
                html_lines.append(f"<li><strong>Total items:</strong> {len(data_dict)}</li>")
                html_lines.append(f"<li><strong>Numeric items:</strong> {count}</li>")
                html_lines.append(f"<li><strong>Total value:</strong> {format_currency(total)}</li>")
                html_lines.append(f"<li><strong>Average value:</strong> {format_currency(avg)}</li>")
                html_lines.append(f"<li><strong>Minimum value:</strong> {format_currency(min_val)}</li>")
                html_lines.append(f"<li><strong>Maximum value:</strong> {format_currency(max_val)}</li>")
                html_lines.append("</ul>")
        
        # Footer
        html_lines.append("<div class='footer'>")
        html_lines.append("<p>End of Report</p>")
        html_lines.append("</div>")
        
        html_lines.append("</body>")
        html_lines.append("</html>")
        
        return "\n".join(html_lines)
    
    # Main function logic
    try:
        # Validate input data
        if not isinstance(data, dict):
            return {
                'success': False,
                'error': f"Input data must be a dictionary, got {type(data).__name__}",
                'input_data': data
            }
        
        if not data:
            return {
                'success': False,
                'error': "Input dictionary is empty",
                'input_data': data
            }
        
        # Validate format_type
        valid_formats = ['text', 'markdown', 'html_simple']
        if format_type not in valid_formats:
            return {
                'success': False,
                'error': f"Invalid format_type: {format_type}. Must be one of: {', '.join(valid_formats)}",
                'input_data': data
            }
        
        # Generate report based on format type
        if format_type == 'text':
            report_content = generate_text_report(data, report_title, include_summary, include_percentages, sort_by_value)
        elif format_type == 'markdown':
            report_content = generate_markdown_report(data, report_title, include_summary, include_percentages, sort_by_value)
        else:  # html_simple
            report_content = generate_html_simple_report(data, report_title, include_summary, include_percentages, sort_by_value)
        
        # Prepare metadata
        metadata = {
            'report_title': report_title,
            'format_type': format_type,
            'data_items_count': len(data),
            'numeric_items_count': sum(1 for v in data.values() if isinstance(v, (int, float))),
            'generation_timestamp': datetime.now().isoformat(),
            'options_used': {
                'include_summary': include_summary,
                'include_percentages': include_percentages,
                'sort_by_value': sort_by_value
            }
        }
        
        # Calculate total if there are numeric values
        numeric_values = [float(v) for v in data.values() if isinstance(v, (int, float))]
        if numeric_values:
            metadata['total_value'] = sum(numeric_values)
            metadata['average_value'] = sum(numeric_values) / len(numeric_values)
        
        return {
            'success': True,
            'report_content': report_content,
            'metadata': metadata,
            'input_data': data,
            'report_length': len(report_content),
            'message': f"Report generated successfully in {format_type} format"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Report generation error: {str(e)}",
            'input_data': data
        }