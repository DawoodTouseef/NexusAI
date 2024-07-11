import "./Sidebar.css";
import { assets } from "../../assets/assets";
import { useContext, useState } from "react";
import { Context } from "../../context/Context";
const Sidebar = () => {
    const [extended, setExtended] = useState(false);
    const { onSent, prevPrompts, setRecentPrompt, newChat,prevresponse } = useContext(Context);

    const loadPreviousPrompt = async (prompt) => {
        setRecentPrompt(prompt);
        await onSent(prompt);
    };
    return (
        <div className="sidebar">
            <div className="top">
                <img
                    src={assets.menu_icon}
                    className="menu"
                    alt="menu-icon"
                    onClick={() => {
                        setExtended((prev) => !prev);
                    }}
                />
                <div className="new-chat">
                    <img src={assets.plus_icon} alt="" onClick={() => {
                        newChat()
                    }} />
                    {extended ? <p>New Chat</p> : null}
                </div>
                {extended ? (
                    <div className="recent">
                        <p className="recent-title">Recent</p>
                            <div className="recent-entry" key="1">
                                    <img src={assets.message_icon} alt="" />
                                <a href={{assets}}>Hello</a>
                            </div>
                            
                        
                    </div>
                ) : null}
            </div>
            <div className="bottom">
                <div className="bottom-item recent-entry">
                    <img src={assets.question_icon} alt="" />
                    {extended ? <p>Help</p> : null}
                </div>
                <div className="bottom-item recent-entry">
                    <img src={assets.history_icon} alt="" />
                    {extended ? <p>Activity</p> : null}
                </div>
                <div className="bottom-item recent-entry">
                    <img src={assets.setting_icon} alt="" />
                    {extended ? <p>Settings</p> : null}
                </div>
            </div>
        </div>
    );
};

export default Sidebar;