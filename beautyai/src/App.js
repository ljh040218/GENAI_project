import React from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Login from "./pages/login/login";
import Sign from "./pages/login/signup";
import Home from './components/Home';
import MainFace from './components/MainFace';   

const App = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path='/mainface' element={<MainFace />} />
                <Route path='/home' element={<Home />} />
                <Route path='/login' element={<Login />} />
                <Route path='/signup' element={<Sign />} />
            </Routes>
        </BrowserRouter>
    );
};

export default App;