/**
 * Landslide Risk Mapper - Lightweight Assistant
 *
 * This is a completely independent, rule-based assistant.
 * It does NOT modify the ML model or core risk engine.
 */

const LandslideAssistant = (() => {

    let initialized = false;

    function getText(id, fallback = "Not available") {
        const element = document.getElementById(id);
        if (!element) return fallback;

        const value = element.textContent.trim();
        return value || fallback;
    }

    function getCurrentData() {

        const location =
            getText("dash-location-name", "the selected location");

        const risk =
            getText("dash-risk-score",
                getText("ml-risk-score", "Not available"));

        const riskLevel =
            getText("dash-risk-badge",
                getText("ml-risk-badge", "Not available"));

        const slope =
            getText("ml-slope-value",
                getText("dash-slope-value", "Not available"));

        const elevation =
            getText("ml-elevation-value",
                getText("dash-elevation-value", "Not available"));

        const rainfall =
            getText("dash-rain-72h", "Not available");

        return {
            location,
            risk,
            riskLevel,
            slope,
            elevation,
            rainfall
        };
    }


    function addMessage(message, sender = "assistant") {

        const messages = document.getElementById("assistant-messages");

        if (!messages) return;

        const messageDiv = document.createElement("div");

        messageDiv.className =
            sender === "user"
                ? "assistant-message user-message"
                : "assistant-message bot-message";

        messageDiv.textContent = message;

        messages.appendChild(messageDiv);

        messages.scrollTop = messages.scrollHeight;
    }


    function getResponse(question) {

        const q = question.toLowerCase().trim();
        const data = getCurrentData();

        // Current risk
        if (
            q.includes("current risk") ||
            q.includes("risk now") ||
            q.includes("risk level") ||
            q === "risk"
        ) {
            return `For ${data.location}, the current model risk score is ${data.risk}/100, classified as ${data.riskLevel}.`;
        }


        // Location
        if (
            q.includes("location") ||
            q.includes("where am i") ||
            q.includes("where is this")
        ) {
            return `The currently selected location is ${data.location}.`;
        }


        // Slope
        if (
            q.includes("slope") ||
            q.includes("steep")
        ) {
            return `The current slope value is ${data.slope}. Steeper slopes generally increase landslide susceptibility.`;
        }


        // Elevation
        if (
            q.includes("elevation") ||
            q.includes("height")
        ) {
            return `The current elevation is ${data.elevation}. Elevation is one of the terrain variables considered by the system.`;
        }


        // Rainfall
        if (
            q.includes("rain") ||
            q.includes("rainfall") ||
            q.includes("precipitation")
        ) {
            return `The displayed 72-hour antecedent rainfall is ${data.rainfall}. Heavy or prolonged rainfall can increase landslide susceptibility.`;
        }


        // Model
        if (
            q.includes("model") ||
            q.includes("random forest") ||
            q.includes("machine learning")
        ) {
            return "The system uses a Random Forest machine-learning model trained on the Mendeley landslide susceptibility dataset containing 12,409 samples.";
        }


        // Dataset
        if (
            q.includes("dataset") ||
            q.includes("data used") ||
            q.includes("training data")
        ) {
            return "The machine-learning model was trained using the Mendeley landslide susceptibility dataset with 12,409 samples.";
        }


        // Accuracy
        if (
            q.includes("accuracy") ||
            q.includes("performance") ||
            q.includes("how accurate")
        ) {
            return "The Random Forest model achieved 75.99% accuracy, 74.25% precision, 83.23% recall, 78.48% F1-score and 83.05% ROC-AUC on the held-out test set.";
        }


        // How it works
        if (
            q.includes("how does this work") ||
            q.includes("how does it work") ||
            q.includes("how it works")
        ) {
            return "You select a location, the system retrieves environmental and terrain information, calculates the relevant parameters, and the Random Forest model estimates landslide susceptibility. The result is then displayed on the map and dashboard.";
        }


        // Factors
        if (
            q.includes("factors") ||
            q.includes("what affects") ||
            q.includes("parameters")
        ) {
            return "The system considers terrain and environmental information such as slope, elevation, rainfall and historical landslide information. The Random Forest model currently uses slope and elevation as its prediction features.";
        }


        // Low risk
        if (
            q.includes("low risk") ||
            q.includes("what does low risk mean")
        ) {
            return "Low Risk means the current model estimates relatively low landslide susceptibility for the selected location. It is a screening result, not a guarantee that a landslide cannot occur.";
        }


        // High risk
        if (
            q.includes("high risk") ||
            q.includes("very high risk")
        ) {
            return "A High or Very High Risk result indicates higher estimated landslide susceptibility. The result should be interpreted as regional decision-support information rather than an exact prediction.";
        }


        // Safety
        if (
            q.includes("safe") ||
            q.includes("dangerous") ||
            q.includes("should i")
        ) {
            return "This application is designed for screening and decision support. It does not predict the exact timing of a landslide, so local authorities and official warnings should always be followed.";
        }


        // Help
        if (
            q === "help" ||
            q.includes("what can you do") ||
            q.includes("questions")
        ) {
            return "You can ask me about the current risk, slope, elevation, rainfall, Random Forest model, dataset, model accuracy, or how the Landslide Risk Mapper works.";
        }


        return "I can help with the current risk, slope, elevation, rainfall, model, dataset, accuracy, or how the Landslide Risk Mapper works. Try asking: \"What is the current risk?\"";
    }


    function sendMessage() {

        const input = document.getElementById("assistant-input");

        if (!input) return;

        const question = input.value.trim();

        if (!question) return;

        addMessage(question, "user");

        input.value = "";

        setTimeout(() => {
            const response = getResponse(question);
            addMessage(response, "assistant");
        }, 250);
    }


    function setupQuickQuestions() {

        const buttons =
            document.querySelectorAll(".assistant-quick-question");

        buttons.forEach(button => {

            button.addEventListener("click", () => {

                const question =
                    button.getAttribute("data-question");

                if (!question) return;

                const input =
                    document.getElementById("assistant-input");

                if (input) {
                    input.value = question;
                }

                sendMessage();
            });

        });
    }


    function setup() {

        if (initialized) return;

        initialized = true;

        const sendButton =
            document.getElementById("assistant-send");

        const input =
            document.getElementById("assistant-input");

        const closeButton =
            document.getElementById("assistant-close");

        const openButton =
            document.getElementById("assistant-open");

        const panel =
            document.getElementById("assistant-panel");


        if (sendButton) {
            sendButton.addEventListener("click", sendMessage);
        }


        if (input) {

            input.addEventListener("keydown", event => {

                if (event.key === "Enter") {
                    event.preventDefault();
                    sendMessage();
                }

            });

        }


        if (closeButton && panel) {

            closeButton.addEventListener("click", () => {
                panel.classList.remove("assistant-visible");
            });

        }


        if (openButton && panel) {

            openButton.addEventListener("click", () => {
                panel.classList.toggle("assistant-visible");
            });

        }


        setupQuickQuestions();

        addMessage(
            "Hi! I can explain the current landslide risk, terrain values, rainfall, model and dataset. What would you like to know?"
        );
    }


    return {
        init: setup
    };

})();


document.addEventListener("DOMContentLoaded", () => {
    LandslideAssistant.init();
});