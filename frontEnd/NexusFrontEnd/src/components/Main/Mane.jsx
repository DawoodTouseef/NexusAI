import React, { useContext, useEffect } from "react";
import { Link } from "react-router-dom"; // Import Link from react-router-dom
import "./Main.css";
import { assets } from "../../assets/assets";
import { Context } from "../../context/Context";

const Mane = () => {
  const {
    onSent,
    recentPrompt,
    showResults,
    loading,
    resultData,
    setInput,
    input,
  } = useContext(Context);
  const isAuthenticated=localStorage.getItem("isAuthenticate");
  const handleCardClick = (promptText) => {
    setInput(promptText);
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleInputKeyPress = (e) => {
    if (e.key === "Enter") {
      onSent();
    }
  };
  useEffect(()=>{
    console.log(isAuthenticated)
  },[])
  return (
    <div className="main">
      <div className="nav">
        <p>NexusAI</p>
        {isAuthenticated ? (
          <img src={assets.user_icon} alt="User Avatar" />
        ) : (
          <Link to="/login">Sign In</Link> // Use Link component to navigate to /login
        )}
      </div>
      <div className="main-container">
        {!showResults ? (
          <>
            <div className="greet">
              <p>
                <span>Hello, {localStorage.getItem('username')}</span>
              </p>
              <p>How can I help you today?</p>
            </div>

            <div className="cards">
              <div
                className="card"
                onClick={() =>
                  handleCardClick("Can you write a poem about the color blue?")
                }
              >
                <p>Can you write a poem about the color blue? </p>
                <img src={assets.compass_icon} alt="Icon" />
              </div>
              <div
                className="card"
                onClick={() => handleCardClick("What's the meaning of life?")}
              >
                <p>What's the meaning of life? </p>
                <img src={assets.message_icon} alt="Icon" />
              </div>
              <div
                className="card"
                onClick={() =>
                  handleCardClick(
                    "Can you explain quantum physics in simple terms?"
                  )
                }
              >
                <p>Can you explain quantum physics in simple terms?</p>
                <img src={assets.bulb_icon} alt="Icon" />
              </div>
              <div
                className="card"
                onClick={() => {
                  handleCardClick("What's the meaning of the number 7?");
                }}
              >
                <p>What's the meaning of the number 7? </p>
                <img src={assets.code_icon} alt="Icon" />
              </div>
            </div>
          </>
        ) : (
          <div className="result">
            <div className="result-title">
              <img src={assets.user_icon} alt="User Avatar" />
              <p>{recentPrompt}</p>
            </div>
            <div className="result-data">
              <img src={assets.gemini_icon} alt="Gemini Icon" />
              {loading ? (
                <div className="loader">
                  <hr />
                  <hr />
                  <hr />
                </div>
              ) : (
                <p dangerouslySetInnerHTML={{ __html: resultData }}></p>
              )}
            </div>
          </div>
        )}

        <div className="main-bottom">
          <div className="search-box">
            <input
              onChange={handleInputChange}
              onKeyPress={handleInputKeyPress}
              value={input}
              type="text"
              placeholder="Enter the Prompt Here"
              
            />
            <div>
              <img src={assets.gallery_icon} alt="Icon" />
              <img src={assets.mic_icon} alt="Icon" />
              <img
                src={assets.send_icon}
                alt="Icon"
                onClick={() => {
                  onSent();
                  setInput('')
                }}
              />
            </div>
          </div>
          <div className="bottom-info">
            <p>
              NexusAI may display inaccurate info, including about people, so
              double-check its responses. Your privacy & NexusAI Co.
            </p>
          </div>
          {/* {!isAuthenticated && ( // Show the button only if not authenticated
            <div className="sign-in-button">
              <Link to="/login">Already have an account? Sign In</Link>
            </div>
          )} */}
        </div>
      </div>
     
    </div>
  );
};

export default Mane;
