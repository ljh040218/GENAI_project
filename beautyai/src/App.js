import React from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Login from "./pages/login/login";
import Sign from "./pages/login/signup";
import Home from './components/Home';
import MainFace from './components/MainFace'; 
import FaceResult from './components/FaceResult';  

const App = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path='/mainface' element={<MainFace />} />
                <Route path='/faceresult' element={<FaceResult />} />
                <Route path='/home' element={<Home />} />
                <Route path='/login' element={<Login />} />
                <Route path='/signup' element={<Sign />} />
                <Route path="/" element={<Login />} />

            </Routes>
            
        </BrowserRouter>
    );
};

export default App;