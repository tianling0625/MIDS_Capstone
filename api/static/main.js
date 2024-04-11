var ready = (callback) => {
    if (document.readyState != "loading") callback();
    else document.addEventListener("DOMContentLoaded", callback);
}

ready(() => {
    document.querySelector(".header").style.height = (window.innerHeight * 0.45) + "px";
    fetchLatestQuestions();
});

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("question-form").addEventListener("submit", function(event) {
        event.preventDefault(); // Prevent the form from submitting the traditional way
        submitQuestion();
        addQuestionToList();
    });
});

function submitQuestion() {
    var question = document.querySelector('[name="question"]').value;
    var submitButton = document.querySelector('input[type="submit"]');
    var spinner = document.getElementById('loading-spinner');
    
    // Check if the input is empty
    if (!question.trim()) {
        submitButton.blur(); // Remove focus from the submit button
        return; // Do nothing if the input is empty
    }
    
    spinner.style.display = 'block'; // Show the spinner

    const encodedQuestionText = encodeURIComponent(question);
    let baseUrl = "https://twang0.mids255.com";
    let requestUrl = `${baseUrl}/submit_question?question_text=${encodedQuestionText}`;

    fetch(requestUrl, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
        },
        body: new URLSearchParams({ "question_text": question })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('llm-answer').style.display = 'block';
        document.getElementById('llm-answer').textContent = data.answer;
        addQuestionToList(question);
        fetchLatestQuestions();
        spinner.style.display = 'none'; // Hide the spinner
    })
    .catch((error) => {
        console.error('Error:', error);
        spinner.style.display = 'none'; // Hide the spinner
    });
}

// Function to add the submitted question to the Recently Asked Questions list
function addQuestionToList(question) {
    if (question) {
        var recentQuestionsList = document.getElementById('recent-questions');
        var listItem = document.createElement('li');
        listItem.textContent = question;
        recentQuestionsList.insertBefore(listItem, recentQuestionsList.firstChild); // Add the new question at the top of the list
        document.querySelector('[name="question"]').value = ''; // Clear the input field
    }
}

// Function to fetch and display the latest questions
function fetchLatestQuestions() {
    fetch('https://twang0.mids255.com/latest-questions/')
    .then(response => response.json())
    .then(data => {
        var recentQuestionsList = document.getElementById('recent-questions');
        recentQuestionsList.innerHTML = ''; // Clear the existing list
        data.forEach(item => {
            var listItem = document.createElement('li');
            listItem.textContent = item.Answer + ' - ' + item.Question.trim();
            recentQuestionsList.appendChild(listItem);
        });
    })
    .catch(error => {
        console.error('Error fetching latest questions:', error);
    });
}

document.getElementById('learn-more-btn').addEventListener('click', function() {
    var answer = document.getElementById('llm-answer').textContent;
    if (answer) {
        // Remove "What is" from the answer and trim any leading or trailing whitespace
        var cleanedAnswer = answer.replace(/^What is\s+/, '').trim();
        // Replace spaces with '+' for the Google search query
        var searchQuery = cleanedAnswer.replace(/\s+/g, '+');
        var googleSearchUrl = 'https://www.google.com/search?q=' + searchQuery;
        window.open(googleSearchUrl, '_blank');
    } else {
        alert('Please submit a question first.');
    }
});