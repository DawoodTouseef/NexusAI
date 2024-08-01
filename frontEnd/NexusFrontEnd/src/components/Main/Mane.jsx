import React, { useContext, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Main.css";
import { assets } from "../../assets/assets";
import { Context } from "../../context/Context";
import axiosInstance from "../../utils/axios";

const Mane = ({ isAuthenticated }) => {
  const {
    showResults,
    setInput,
    setRecentPrompt,
    input,
  } = useContext(Context);
  const [title_id, setTitleId] = useState("");
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [shiftEnterCount, setShiftEnterCount] = useState(0);
  const [textareaHeight, setTextareaHeight] = useState("auto");

  const handleCardClick = (promptText) => {
    setInput(promptText);
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleInputKeyPress = async (e) => {
    if (e.key === "Enter" && e.shiftKey) {
      e.preventDefault();
      setShiftEnterCount((prevCount) => {
        const newCount = prevCount + 1;
        if (newCount <= 5) {
          setTextareaHeight((prevHeight) =>
              typeof prevHeight === "number" ? prevHeight + 20 : "100px"
          );
        }
        return newCount;
      });
    } else if (e.key === "Enter") {
      await sendInput();
    }
  };
  const adjustTextareaHeight = (textarea) => {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + "px";
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFile(file);
    }
  };

  const handleGalleryClick = () => {
    fileInputRef.current.click();
  };

  const sendInput = async () => {
    try {
      const formData = new FormData();
      formData.append("title", input);
      setRecentPrompt(input)

      const response = await axiosInstance.post("/new_thread/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const title_id = response.data.title_id;
      setTitleId(title_id);
      navigate(`app/${title_id}`);
      setInput('');
      setFile(null);
    } catch (error) {
      console.error("Error creating new thread:", error);
    }
  };

  useEffect(() => {
    if (title_id) {
      navigate(`app/${title_id}`);
    }
  }, [title_id, navigate]);

  return (
    <div className="main">
      <div className="nav">
        <p>NexusAI</p>
        {isAuthenticated ? (
          <>
          <img src={`${assets.API_URL}/serve${localStorage.getItem('profile_image')}/`} alt="User Avatar" />
        </>
        ) : (
          <Link to="/login">Sign In</Link>
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
        ) : null}

        <div className="main-bottom">
          <div className="search-box">
            <input
              onChange={handleInputChange}
              onKeyPress={handleInputKeyPress}
              value={input}
              type="text"
              placeholder="Enter the Prompt Here"
              style={{
                height: shiftEnterCount > 5 ? "150px" : textareaHeight,
                overflowY: shiftEnterCount > 5 ? "scroll" : "hidden",
              }}
            />
            <div>
              <img src={assets.gallery_icon} alt="Icon" onClick={handleGalleryClick} />
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              <img src={assets.mic_icon} alt="Icon" />
              <img
                src={assets.send_icon}
                alt="Icon"
                onClick={sendInput}
              />
            </div>
          </div>
          <div className="bottom-info">
            <p>
              NexusAI may display inaccurate info, including about people, so
              double-check its responses. Your privacy & NexusAI Co.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Mane;
