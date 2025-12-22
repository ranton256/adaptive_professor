Feature: Hello World - Basic System Connectivity
  As a developer
  I want to verify the basic system setup works
  So that I can build upon a working foundation

  Scenario: Backend health check
    Given the backend server is running
    When I request the health endpoint
    Then I should receive a 200 OK response
    And the response should contain "status": "healthy"

  Scenario: Frontend loads successfully
    Given the frontend application is running
    When I navigate to the home page
    Then I should see the application title
    And the page should load without errors

  Scenario: Frontend can communicate with backend
    Given the backend server is running
    And the frontend application is running
    When the frontend requests the backend health endpoint
    Then the frontend should display the connection status as "connected"
