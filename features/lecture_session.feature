Feature: Lecture Session
  As a learner
  I want to receive an adaptive lecture experience
  So that I can learn at my own pace and depth

  Background:
    Given the backend server is running
    And the frontend application is running
    And I am on the home page

  # Scenario: Start a lecture from a topic
  #   When I enter the topic "Introduction to Rust Ownership"
  #   And I click "Start Lecture"
  #   Then I should see the first slide rendered
  #   And the slide should have a title
  #   And I should see navigation options

  # Scenario: Navigate to next slide
  #   Given I have started a lecture on "Introduction to Rust Ownership"
  #   And I am viewing a slide
  #   When I click the "Next" button
  #   Then I should see the next slide in the main thread
  #   And the slide transition should be smooth

  Scenario: Request clarified explanation
    Given I have started a lecture on "Introduction to Rust Ownership"
    And I am viewing a slide with technical content
    When I click the "Clarify" button
    Then the current slide should be rewritten
    And the explanation should be clearer with defined terms
    And the core concepts should remain the same
