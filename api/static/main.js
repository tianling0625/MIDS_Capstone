var ready = (callback) => {
    if (document.readyState != "loading") callback();
    else document.addEventListener("DOMContentLoaded", callback);
}

ready(() => {
    document.querySelector(".header").style.height = window.innerHeight + "px";
});

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("question-form").addEventListener("submit", function(event) {
        event.preventDefault(); // Prevent the form from submitting the traditional way
        submitQuestion();
    });
});

function submitQuestion() {
    var question = document.querySelector('[name="question"]').value;
    console.log(question)
    const encodedQuestionText = encodeURIComponent(question);
    console.log(encodedQuestionText)

    let baseUrl = window.location.href.includes("https://twang0.mids255.com") ? "https://twang0.mids255.com" : "http://localhost:8000";
    let requestUrl = `http://localhost:8000/submit_question?question_text=${encodedQuestionText}`;
    
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
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

