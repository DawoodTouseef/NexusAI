import { createContext, useState } from "react";
import {runChat,runlocal} from "../config/gemini";

export const Context = createContext();

  
const ContextProvider = (props) => {
    const [input, setInput] = useState("");
    const [recentPromptFROMMAIN, setRecentPrompt] = useState("");
    const [prevPrompts, setPrevPrompts] = useState([]);
    const [prevresponse, setresponse] = useState([]);
    const [showResults, setShowResults] = useState(false);
    const [loading, setLoading] = useState(false);
    const [resultData, setResultData] = useState("");
    const delayPara = (index, nextWord) => {
        setTimeout(function () {
            setResultData((prev) => prev + nextWord);
        }, 10 * index);
    };
    const newChat = () => {
        setLoading(false);
        setShowResults(false)
    }

    const onSentDyanamic = async (prompt,file=null) => {
        setResultData("");
        setLoading(true);
        setShowResults(true);
        const formData = new FormData();
        if (file){
            formData.append('file', file);
        }
        setRecentPrompt(prompt);
    };

    const contextValue = {
        prevPrompts,
        setPrevPrompts,
        onSentDyanamic,
        setRecentPrompt,
        recentPromptFROMMAIN,
        input,
        setInput,
        showResults,
        loading,
        resultData,
        newChat,
        setresponse,
        prevresponse,
    };

    return (
        <Context.Provider value={contextValue}>{props.children}</Context.Provider>
    );
};

export default ContextProvider;