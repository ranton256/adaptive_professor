Feature: A2UI Streaming Protocol
  As a system
  I want to stream UI components progressively
  So that users experience low perceived latency

  Background:
    Given the backend server is running
    And the frontend application is running

  Scenario: Slide skeleton renders immediately
    Given I have started a lecture
    When a new slide is being generated
    Then the slide skeleton should render within 100ms
    And the content should stream in progressively

  Scenario: Dynamic action buttons are rendered
    Given I am viewing a slide about "The Gracchi Brothers"
    Then I should see context-aware action buttons
    And one button should offer a deep dive into "The Gracchi Brothers"
    And the buttons should be generated from the slide content

  Scenario: Component type changes based on agent decision
    Given I am in a lecture session
    When the agent decides to show a code example
    Then a CodeBlock component should be rendered
    When the agent decides to show a quiz
    Then a QuizWidget component should be rendered

  Scenario: JSONL streaming maintains state
    Given I am in an active lecture session
    When the backend streams a slide payload
    Then the payload should include slide content
    And the payload should include interactive controls
    And the payload should indicate allowed actions
