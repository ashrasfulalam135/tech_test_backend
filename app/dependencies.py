import sqlparse
import sqlvalidator
import hashlib
import re

def sqlparser(sql_query):
    process = True
    if is_select_statement(sql_query):
        # Attempt to check it is a select statement or not. if the select statement it goes throw the validation check
        if not validate_sql_query(sql_query):
            process = False
            
    if not process:
        return False
    
    column_name_mapping = hash_column_names(sql_query)
    modified_sql = modified_query(sql_query, column_name_mapping)
    
    return column_name_mapping, modified_sql

def is_select_statement(sql_query):
    try:
        # Parse the SQL query using sqlparse
        parsed = sqlparse.parse(sql_query)
        # Check if the first statement is a SELECT statement
        if parsed and parsed[0].get_type() == 'SELECT':
            return True
        return False
    except Exception as e:
        # Handle parsing errors gracefully
        return False

def validate_sql_query(sql_query):
    try:
        # Attempt to parse the SQL query to check for syntax errors
        parsed = sqlvalidator.parse(sql_query)
        if not parsed.is_valid():
            return False  # The query is invalid
        return True  # The query is valid
    except Exception as e:
        return False  # An exception occurred, indicating an invalid query

def hash_column_names(sql_query):
    try:
        # Parse the SQL query using sqlparse
        parsed = sqlparse.parse(sql_query)
        column_name_mapping = {}
        process_token = True
        # Traverse the parsed SQL tokens and build the mapping
        for statement in parsed:
            parse_statement(statement, column_name_mapping, process_token)

        return column_name_mapping
    except Exception as e:
        # Handle parsing errors gracefully
        print(f"Error parsing SQL: {str(e)}")
        return {}, set()

def flag_controller(token, process_token):
    # ditect which token has to be processed or not
    if token.ttype == sqlparse.tokens.DML and token.value.upper() == 'UPDATE':
        # This token indicates the start of the UPDATE clause
        process_token = False
    if token.ttype == sqlparse.tokens.Keyword and token.value.upper() == 'FROM':
        # This token indicates the start of the FROM clause
        process_token = False
    if token.ttype == sqlparse.tokens.Keyword and (token.value.upper() == 'INNER JOIN' or token.value.upper() == 'LEFT JOIN' or token.value.upper() == 'RIGHT JOIN' or token.value.upper() == 'FULL OUTER JOIN' or token.value.upper() == 'FULL OUTER JOIN'):
        # This token indicates the start of the JOIN clause
        process_token = False
    if isinstance(token, sqlparse.sql.Where):
        # This token indicates the start of the Where clause
        process_token = True
    if token.ttype == sqlparse.tokens.Keyword and (token.value.upper() == 'ON' or token.value.upper() == 'SET'):
        # This token indicates the start of the ON clause
        process_token = True
    return process_token

def parse_statement(statement, column_name_mapping, process_token):
    for token in statement.tokens:
        process_token = flag_controller(token, process_token)

        if process_token:
            if token.ttype == sqlparse.tokens.Wildcard:
                # This token represents wildcard (*)
                map_original_hashed_column_name("*", column_name_mapping)
            elif isinstance(token, sqlparse.sql.Identifier):
                # This token represents an identifier
                map_original_hashed_column_name(
                    token.get_real_name(), column_name_mapping)
            elif isinstance(token, sqlparse.sql.IdentifierList):
                # This token represents a list of identifiers ( For multiple column selection)
                for indentifier_list_token in token.tokens:
                    if isinstance(indentifier_list_token, sqlparse.sql.Function):
                        for function_token in indentifier_list_token.tokens:
                            if isinstance(function_token, sqlparse.sql.Parenthesis):
                                for identifier_token_inside_function in function_token.tokens:
                                    if isinstance(identifier_token_inside_function, sqlparse.sql.Identifier):
                                        map_original_hashed_column_name(
                                            identifier_token_inside_function.get_real_name(), column_name_mapping)
                    elif isinstance(indentifier_list_token, sqlparse.sql.Identifier):
                        map_original_hashed_column_name(
                            indentifier_list_token.get_real_name(), column_name_mapping)
                    elif isinstance(indentifier_list_token, sqlparse.sql.Comparison):
                        # This token represents an Comparisons
                        for comparison_token in indentifier_list_token.tokens:
                            if isinstance(comparison_token, sqlparse.sql.Identifier):
                                map_original_hashed_column_name(
                                    comparison_token.get_real_name(), column_name_mapping)
            elif isinstance(token, sqlparse.sql.Comparison):
                # This token represents an Comparisons
                for comparison_token in token.tokens:
                    if isinstance(comparison_token, sqlparse.sql.Identifier):
                        map_original_hashed_column_name(
                            comparison_token.get_real_name(), column_name_mapping)
            elif isinstance(token, sqlparse.sql.Function):
                # This token represents a function in INSERT query statement
                for function_token in token.tokens:
                    if isinstance(function_token, sqlparse.sql.Parenthesis):
                        for identifier_token_inside_function in function_token.tokens:
                            if identifier_token_inside_function.ttype == sqlparse.tokens.Wildcard:
                                # This token represents wildcard (*)
                                map_original_hashed_column_name(
                                    "*", column_name_mapping)
                            elif isinstance(identifier_token_inside_function, sqlparse.sql.Identifier):
                                map_original_hashed_column_name(
                                    identifier_token_inside_function.get_real_name(), column_name_mapping)
                            elif isinstance(identifier_token_inside_function, sqlparse.sql.IdentifierList):
                                for identifier_inside_function in identifier_token_inside_function.get_identifiers():
                                    map_original_hashed_column_name(
                                        identifier_inside_function.get_real_name(), column_name_mapping)
            elif isinstance(token, sqlparse.sql.Parenthesis):
                for parenthesis_token in token.tokens:
                    if isinstance(parenthesis_token, sqlparse.sql.Identifier):
                        map_original_hashed_column_name(
                            parenthesis_token.get_real_name(), column_name_mapping)
                    elif isinstance(parenthesis_token, sqlparse.sql.IdentifierList):
                        for identifier_parenthesis in parenthesis_token.get_identifiers():
                            map_original_hashed_column_name(
                                identifier_parenthesis.get_real_name(), column_name_mapping)
            elif isinstance(token, sqlparse.sql.Where):
                for where_token in token.tokens:
                    if isinstance(where_token, sqlparse.sql.Comparison):
                        # This token represents condition inside where clause
                        for comparison_token in where_token.tokens:
                            if isinstance(comparison_token, sqlparse.sql.Identifier):
                                map_original_hashed_column_name(
                                    comparison_token.get_real_name(), column_name_mapping)
                    elif isinstance(where_token, sqlparse.sql.Identifier):
                        # This token represents Indentifier inside where clause
                        map_original_hashed_column_name(
                            where_token.get_real_name(), column_name_mapping)
                    elif isinstance(where_token, sqlparse.sql.Parenthesis):
                        # This will check nested query and rerun to find the columns.
                        nested_query = where_token.value.replace(
                            "(", "").replace(")", "")
                        hash_column_names(nested_query)

def map_original_hashed_column_name(original_column_name, column_name_mapping):
    # Hash the original column name
    hashed_column_name = hashlib.sha256(
        original_column_name.encode()).hexdigest()
    # Update the mapping
    column_name_mapping[original_column_name] = hashed_column_name

def modified_query(sql_query, column_name_mapping):
    # Generate the dynamic regular expression pattern based on keys in the column_mapping
    column_pattern = re.compile(r'\b(' + '|'.join(re.escape(key) for key in column_name_mapping.keys()) + r')\b')

    # Replace column names with mapped values using regular expressions
    modified_query = column_pattern.sub(lambda match: column_name_mapping[match.group(0)], sql_query)

    return modified_query
