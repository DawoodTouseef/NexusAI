import "./Sidebar.css";
import { assets } from "../../assets/assets";
import { useContext, useState } from "react";
import { Context } from "../../context/Context";
import axiosInstance from "../../utils/axios"
import { Link } from 'react-router-dom';

const Sidebar = () => {
    const [extended, setExtended] = useState(false);
    const { onSent,newChat} = useContext(Context);
    const [thread, setthreads] = useState([]);
    const loadPreviousPrompt = async () => {
        const url=assets.API_URL;
        const response = await axiosInstance.post("/threads/");
        const threads=response.data;
        setthreads(threads);
    };
    loadPreviousPrompt();
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
                    <Link to={"/"}>
                    <img src={assets.plus_icon} alt="" />
                    </Link>
                    {extended ? <Link to={"/"} style={{"textDecoration":"none","color":"silver"}}>
                    <p>New chat</p>
                    </Link> : null}
                </div>
                {extended ? (
                    <div className="recent">
                        <p className="recent-title">Recent</p>
                        {thread.map((item, index) => (
                            <Link to={`app/${item.title_id}`} key={index} className="recent-entry" style={{"textDecoration":"none"}}>
                                <img src={assets.message_icon} alt="" />
                                <p>{item.title}</p>
                            </Link>
                        ))}
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