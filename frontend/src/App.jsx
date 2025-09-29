import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Bar, Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import './App.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend);

const AgentResponse = ({ data }) => {
    const responseData = data.answer || data;
    if (!responseData || !responseData.summary) return null;

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { 
                position: 'top',
                labels: { color: '#e5e7eb', font: { size: 14 } }
            },
            title: { 
                display: false // We'll use our own title
            },
        },
        maintainAspectRatio: false,
        scales: {
            x: {
                ticks: { color: '#d1d5db', font: { size: 12 } },
                grid: { color: 'rgba(75, 85, 99, 0.5)' }
            },
            y: {
                ticks: { color: '#d1d5db', font: { size: 12 } },
                grid: { color: 'rgba(75, 85, 99, 0.5)' }
            }
        }
    };
    
    const hasVisuals = (responseData.chartType !== 'NONE' && responseData.chartData) || 
                      (responseData.tableData && responseData.tableData.rows && responseData.tableData.rows.length > 0);

    return (
        <div className="agent-response-grid">
            <div className="summary-panel">
                <h3 className="panel-title">Analysis Summary</h3>
                <p className="summary-text">{responseData.summary}</p>
            </div>
            
            {hasVisuals && (
                <div className="visualization-panel">
                    <h3 className="panel-title">Visualizations</h3>
                    {responseData.chartType === 'BAR' && responseData.chartData && (
                        <div className="chart-wrapper"><Bar options={chartOptions} data={responseData.chartData} /></div>
                    )}
                    {responseData.chartType === 'LINE' && responseData.chartData && (
                        <div className="chart-wrapper"><Line options={chartOptions} data={responseData.chartData} /></div>
                    )}
                    {responseData.tableData && responseData.tableData.headers && responseData.tableData.rows && responseData.tableData.rows.length > 0 && (
                        <div className="table-wrapper">
                            <table>
                                <thead><tr>{responseData.tableData.headers.map((h, i) => <th key={i}>{h}</th>)}</tr></thead>
                                <tbody>{responseData.tableData.rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

const ChatMessage = ({ message }) => (
    <div className={`message ${message.sender}`}>
        {message.sender === 'agent' ? <AgentResponse data={message.data} /> : message.text}
    </div>
);

function App() {
    const [file, setFile] = useState(null);
    const [messages, setMessages] = useState([
        { sender: 'agent', data: { summary: "Hello! I'm your AI Data Agent. You can ask me general questions, or upload a file to begin a deeper analysis." } }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    useEffect(scrollToBottom, [messages]);

    const handleFileChange = async (e) => {
        const selectedFile = e.target.files[0];
        if (!selectedFile) return;
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        try {
            setIsLoading(true);
            await axios.post('http://localhost:8000/uploadfile/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            setFile(selectedFile);
            setMessages(prev => [...prev, { sender: 'agent', data: { summary: `Your file "${selectedFile.name}" has been successfully processed. I'm ready to help. What would you like to know?` } }]);
        } catch (error) {
            alert('File upload failed. Please check the server connection and try again.');
        } finally {
            setIsLoading(false);
            e.target.value = null; 
        }
    };

    const handleQuery = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = { sender: 'user', text: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const payload = { question: input, filename: file ? file.name : null };
            const response = await axios.post('http://localhost:8000/query/', payload);
            const agentMessage = { sender: 'agent', data: response.data };
            setMessages(prev => [...prev, agentMessage]);
        } catch (error) {
            const errorMessage = { sender: 'agent', data: { summary: "Sorry, an error occurred while processing your request." } };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const clearFileContext = () => {
        setFile(null);
        setMessages(prev => [...prev, { sender: 'agent', data: { summary: "File context has been cleared. I am now answering questions based on general knowledge." } }])
    };

    return (
        <div className="App">
            <header className="header"><h1>AI Data Agent 🧠</h1></header>
            <main className="main-content">
                <div className="chat-container">
                    <div className="file-status-bar">
                        <label htmlFor="file-upload" className="custom-file-upload">
                            📎 {file ? `Active: ${file.name}` : "Upload File for Analysis"}
                        </label>
                        <input id="file-upload" type="file" onChange={handleFileChange} />
                        {file && <button onClick={clearFileContext} className="clear-file-btn">Clear File</button>}
                    </div>
                    <div className="messages">
                        {messages.map((msg, index) => <ChatMessage key={index} message={msg} />)}
                        {isLoading && <div className="message agent loading-dots"><span></span><span></span><span></span></div>}
                        <div ref={messagesEndRef} />
                    </div>
                    <form onSubmit={handleQuery} className="input-form">
                        <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a question..." disabled={isLoading}/>
                        <button type="submit" disabled={isLoading}>Send</button>
                    </form>
                </div>
            </main>
        </div>
    );
}

export default App;

