import "./Sidebar.css";
import { assets } from "../../assets/assets";
import { useState, useEffect } from "react";
import axiosInstance from "../../utils/axios";
import { Link, useNavigate } from 'react-router-dom';
import { DotsThreeVertical, SignOut } from "@phosphor-icons/react";
import Dropdown from 'react-bootstrap/Dropdown';

const Sidebar = () => {
    const [extended, setExtended] = useState(false);
    const [threads, setThreads] = useState([]);
    const [dropdownVisible, setDropdownVisible] = useState(null);
    const navigate = useNavigate();

    const loadPreviousPrompt = async () => {
        const response = await axiosInstance.get("/threads/");
        const threads = response.data;
        setThreads(threads);
    };

    useEffect(() => {
        loadPreviousPrompt();
    }, []);

    const toggleDropdown = (index) => {
        setDropdownVisible(dropdownVisible === index ? null : index);
    };
    const truncateText = (text, maxLength) => {
        return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
    };
    return (
        <>
            <div className={`sidebar ${extended ? 'extended' : ''}`}>
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
                        <Link to={"/"} style={{textDecoration: "none", color: "silver"}}/>
                        <img src={assets.plus_icon} alt=""/>
                        {extended ? (
                            <Link to={"/"} style={{textDecoration: "none", color: "silver"}}>
                                <p>New chat</p>
                            </Link>
                        ) : null}
                    </div>
                    {extended && (
                        <div className="recent">
                            <p className="recent-title">Recent</p>
                            {threads.map((item, index) => (
                                <div key={index} className="recent-entry-container">
                                    <Link to={`/app/${item.title_id}`} className="recent-entry"
                                          style={{textDecoration: "none"}}>
                                        <img src={assets.message_icon} alt=""/>
                                        <p>{truncateText(item.title, 15)}</p>
                                        <DotsThreeVertical
                                            size={20}
                                            onClick={() => toggleDropdown(index)}
                                        />
                                        {dropdownVisible === index && (
                                            <Dropdown>
                                                <Dropdown.Toggle variant="success" id="dropdown-basic">
                                                    {/* Empty Toggle as the trigger is the DotsThreeVertical */}
                                                </Dropdown.Toggle>
                                                <Dropdown.Menu>
                                                    <Dropdown.Item href="#/action-1">Pin</Dropdown.Item>
                                                    <Dropdown.Item href="#/action-2">Rename</Dropdown.Item>
                                                    <Dropdown.Item href="#/action-3">Delete</Dropdown.Item>
                                                    <Dropdown.Item onClick={() => {
                                                        setDropdownVisible(false)
                                                    }}>Close</Dropdown.Item>
                                                </Dropdown.Menu>
                                            </Dropdown>
                                        )}
                                    </Link>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                <div className="bottom">
                    <div className="bottom-item recent-entry">
                        <img src={assets.question_icon} alt=""/>
                        {extended && <p>Help</p>}
                    </div>
                    <div className="bottom-item recent-entry">
                        <img src={assets.history_icon} alt=""/>
                        {extended && <p>Activity</p>}
                    </div>
                    <div className="bottom-item recent-entry">
                        <img src={assets.setting_icon} alt=""/>
                        {extended && <p>Settings</p>}
                    </div>
                    <div className="bottom-item recent-entry">
                        <SignOut size={22} onClick={() => navigate("/logout")}/>
                        {extended && <p onClick={() => navigate("/logout")}>Logout</p>}
                    </div>
                </div>
            </div>
        </>
    );
};
export default Sidebar;

