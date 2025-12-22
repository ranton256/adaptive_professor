Feature: Interactive Learning
  As a learner
  I want to explore topics in depth and ask questions
  So that I can satisfy my curiosity and deepen understanding

  Background:
    Given the backend server is running
    And the frontend application is running
    And I have started a lecture on "Introduction to Rust Ownership"

  Scenario: Deep dive into a specific concept
    Given I am viewing a slide that mentions "The Borrow Checker"
    When I click the "Deep Dive: The Borrow Checker" button
    Then a sub-thread should be created
    And I should see slides explaining the borrow checker in detail
    And I should have an option to "Return to Lecture"

  Scenario: Return from deep dive to main thread
    Given I am in a deep dive sub-thread
    When I click "Return to Lecture"
    Then I should return to the main thread
    And I should be at the slide after where I branched

  Scenario: Ask a freeform question (Raise Hand)
    Given I am viewing a slide about memory management
    When I type the question "How does this compare to garbage collection?"
    And I submit the question
    Then the agent should generate a detour slide
    And the slide should answer my specific question
    And I should have an option to continue the main lecture

  Scenario: Quiz me on current content
    Given I am viewing a slide with key concepts
    When I click the "Quiz Me" button
    Then I should see a quiz component
    And the quiz should test understanding of the current slide
    And I should be able to submit my answer
    And I should receive feedback on my answer
