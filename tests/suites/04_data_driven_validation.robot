*** Settings ***
Resource        ../keywords/payment_keywords.robot
Library         Collections
Library         OperatingSystem
Library         String
Suite Setup     Run Keywords    Create Payment Session    AND    Reset Test State

*** Test Cases ***

Data Driven IBAN Validation From CSV
    [Documentation]    Reads iban_validation.csv and validates each row against the API
    [Tags]    data-driven    validation
    ${csv_path}=    Set Variable    ${CURDIR}/../data/iban_validation.csv
    ${raw}=    Get File    ${csv_path}
    ${lines}=    Split To Lines    ${raw}
    # Skip header row
    ${data_rows}=    Get Slice From List    ${lines}    1
    FOR    ${line}    IN    @{data_rows}
        ${line}=    Strip String    ${line}
        Continue For Loop If    '${line}' == ''
        @{cols}=    Split String    ${line}    ,
        ${iban}=          Strip String    ${cols}[0]
        ${currency}=      Strip String    ${cols}[1]
        ${exp_valid}=     Strip String    ${cols}[2]
        ${exp_reason}=    Strip String    ${cols}[3]
        ${description}=   Strip String    ${cols}[4]
        Log    Testing: ${description} | IBAN: ${iban}    console=True
        ${resp}=    Validate IBAN    ${iban}    ${currency}
        Should Be Equal As Integers    ${resp.status_code}    200
        ${body}=    Set Variable    ${resp.json()}
        ${is_valid}=    Evaluate    '${exp_valid}'.strip().lower() == 'true'
        IF    ${is_valid}
            Should Be True    ${body}[valid]    msg=Expected valid for: ${description}
        ELSE
            Should Not Be True    ${body}[valid]    msg=Expected invalid for: ${description}
            IF    '${exp_reason}' != ''
                Should Be Equal    ${body}[reason]    ${exp_reason}
            END
        END
    END
