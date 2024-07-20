import React, { useContext, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import "./Main.css";
import { assets } from "../../assets/assets";
import axiosInstance from "../../utils/axios";
import { runlocal } from "../../config/gemini";
import { convert } from 'html-to-text';
import { SpeakerHigh, SpeakerNone } from "@phosphor-icons/react";
import { Context } from "../../context/Context";


const DyanamicMain = () => {
  const { title_id } = useParams();
  const { recentPromptFROMMAIN } = useContext(Context);
  const [recentPrompt, setRecentPrompt] = useState("");
  const [input, setInput] = useState("");
  const [thread, setThreads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState("");
  const [showResults, setShowResults] = useState(false);
  const isAuthenticated = localStorage.getItem('isAuthenticated');
  const fileInputRef = useRef(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [speakingIndex, setSpeakingIndex] = useState(-1);
  const [showGallery]=useState(false);
  const handleInputKeyPress = (e) => {
    if (e.key === "Enter") {
      onSent();
      setInput("");
      setUploadedFile(null);
    }
  };

  const loadPreviousPrompt = async () => {
    const response = await axiosInstance.post(`/thread_info/${title_id}/`);
    const threads = response.data;
    setThreads(threads.response);
  };

  const text_to_speech = (text, index) => {
    const utterance = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utterance);
    setSpeakingIndex(index);
  };

  const stoptts = () => {
    speechSynthesis.cancel();
    setSpeakingIndex(-1);
  };
  const Loadchats = () => {
    return (
      <>
        {thread.map((item, index) => (
          <React.Fragment key={index}>
            <div className="result-title" key={`${item.user}-${item.id}`}>
              <img src={`${assets.API_URL}/serve${localStorage.getItem('profile_image')}/`} alt="User Avatar" />
              <p>{item.user}</p>
              <div style={{ marginRight: '10px' }}>
                {speakingIndex !== index ? (
                  <SpeakerHigh size={20} onClick={() => text_to_speech(item.assistant, index)} />
                ) : (
                  <SpeakerNone size={20} onClick={stoptts} />
                )}
              </div>
            </div>
            <div className="result-data" key={`${item.assistant}-${item.id}`}>
              <img src={assets.gemini_icon} alt="Gemini Icon" />
              <p dangerouslySetInnerHTML={{ __html: history(item.assistant) }}></p>
            </div>
            <div className="bottom-info">
              {item.path && item.path.length > 0 ? (
                <img src={`${assets.API_URL}/serve${item.path[0].image}/`} alt="Image" style={{ width: "50%", height: "70%" }} />
              ) : null}
            </div>
          </React.Fragment>
        ))}
      </>
    );
  };
  const history = (text) => {
    const options = {
      wordwrap: 130,
    };
  
    const convertedText = convert(text, options);
  
    const codeBlockRegex = /```([^`]*)```/gs;
    const inlineCodeRegex = /`([^`]*)`/g;
    const boldItalicRegex = /\*\*\*([^*]+)\*\*\*/g;
    const boldRegex = /\*\*([^*]+)\*\*/g;
    const italicRegex = /\*([^*]+)\*/g;
    const headingRegex = /^(#+)\s(.+)/gm;
    const blockquoteRegex = /^>\s(.+)/gm;
    const unorderedListRegex = /^\s*[-*]\s(.+)/gm;
    const orderedListRegex = /^\s*\d+\.\s(.+)/gm;
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    const hrRegex = /^---$/gm;
    
    let formattedText = convertedText.replace(codeBlockRegex, (match, p1) => `<pre><code>${p1.trim()}</code></pre>`);
  
    formattedText = formattedText.replace(inlineCodeRegex, (match, p1) => `<code>${p1}</code>`);
  
    formattedText = formattedText.replace(boldItalicRegex, (match, p1) => `<b><i>${p1}</i></b>`);
  
    formattedText = formattedText.replace(boldRegex, (match, p1) => `<br><b>${p1}</b>`);
  
    formattedText = formattedText.replace(italicRegex, (match, p1) => `<i>${p1}</i>`);

    formattedText = formattedText.replace(headingRegex, (match, p1, p2) => {
      const level = p1.length;
      return `<h${level}>${p2}</h${level}>`;
    });
  
    formattedText = formattedText.replace(blockquoteRegex, (match, p1) => `<blockquote>${p1}</blockquote>`);
  
    formattedText = formattedText.replace(unorderedListRegex, (match, p1) => `<ul><li>${p1}</li></ul>`);
  
    formattedText = formattedText.replace(orderedListRegex, (match, p1) => `<ol><li>${p1}</li></ol>`);
  
    formattedText = formattedText.replace(linkRegex, (match, p1, p2) => `<a href="${p2}" target="_blank">${p1}</a>`);
  
    formattedText = formattedText.replace(hrRegex, () => `<hr>`);

    return formattedText;
  };
  

  const handleGalleryClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setUploadedFile(file);
    setInput(file.name);
  };

  const handleDeleteFile = () => {
    setUploadedFile(null);
    setInput("");
  };

  useEffect(() => {
    loadPreviousPrompt();
    if (recentPromptFROMMAIN) {
      setInput(recentPromptFROMMAIN);
    }
  }, [title_id]);

  const onSent = async (prompt = input) => {
    // Append user input to the thread
    setThreads((prevThreads) => [
      ...prevThreads,
      {
        user: prompt,
        assistant: "<div className=\"loader\">\n" +
            "                    <hr />\n" +
            "                    <hr />\n" +
            "                    <hr />\n" +
            "                  </div>",
        id: Date.now(), // Temporary ID
        path: [],
      },
    ]);
    setResultData("");
    setLoading(true);
    setShowResults(true);
    let 
        response;
    let path;
    if (prompt !== undefined) {
      response,path = await runlocal(prompt, uploadedFile, title_id);
      console.log(response)
      console.log(path)
      setRecentPrompt(prompt);
    }

    try {
      let newResponse2=history(response);
      let newResponseArray = newResponse2.split("");
      for (let i = 0; i < newResponseArray.length; i++) {
        const nextWord = newResponseArray[i];
        delayPara(i, nextWord + "");
      }
      setThreads((prevThreads) =>
          prevThreads.map((item) =>
              item.id === Date.now()
                  ? { ...item, assistant: newResponse2 }
                  : item
          )
      );
    } catch (error) {
      console.error("Error while running chat:", error);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  const delayPara = (index, nextWord) => {
    setTimeout(function () {
      setResultData((prev) => prev + nextWord);
    }, 10 * index);
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const settts = (text) => () => {
    text_to_speech(text);
  };

  return (
    <div className="main">
      <div className="nav">
        <p>NexusAI</p>
        {isAuthenticated ? (
          <img src={`${assets.API_URL}/serve${localStorage.getItem('profile_image')}/`} alt="User Avatar" />
        ) : (
          <Link to="/login">Sign In</Link>
        )}
      </div>
      <div className="main-container">
        <div className="result">
          {!recentPrompt ? <Loadchats /> : null}
          {recentPrompt && (
            <>
              <div className="result-title">
                <img src={`${assets.API_URL}/serve${localStorage.getItem('profile_image')}/`} alt="User Avatar" />
                <p>{recentPrompt}</p>
              </div>
              <div className="result-data">
                <SpeakerHigh size={15} onClick={settts(history(resultData))} />
                <img src={assets.gemini_icon} alt="Gemini Icon" />
                {loading && showResults ? (
                  <div className="loader">
                    <hr />
                    <hr />
                    <hr />
                  </div>
                ) : (
                  <>
                    <p dangerouslySetInnerHTML={{ __html: resultData }}></p>
                    {showGallery ? showGallery : null}
                  </>
                )}
              </div>
            </>
          )}
        </div>
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
              {uploadedFile && (
                <span className="uploaded-file">
                  {uploadedFile.name}
                  <button onClick={handleDeleteFile}>&times;</button>
                </span>
              )}
              <img src={assets.gallery_icon} alt="Gallery Icon" onClick={handleGalleryClick} />
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
                onClick={() => {
                  onSent();
                  setInput('');
                }}
              />
            </div>
          </div>
          <div className="bottom-info">
            <p>
              NexusAI may display inaccurate info, including about people, so
              double-check its responses.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DyanamicMain;
