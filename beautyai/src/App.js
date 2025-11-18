import React from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Login from "./pages/login/login";
import Sign from "./pages/login/signup";
import Home from './components/Home';
import MainFace from './components/MainFace'; 
import FaceResult from './components/FaceResult';  
import ProductResult from './components/ProductResult';
import MainProduct from './components/MainProduct';
import Profile from './pages/login/ProfileSCreate';
import ProfileEdit from './pages/login/ProfileEdit';
import ProfileView from './pages/login/ProfileView';    

const App = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path='/mainface' element={<MainFace />} />
                <Route path='/mainproduct' element={<MainProduct />} />
                <Route path='/faceresult' element={<FaceResult />} />
                <Route path='/productresult' element={<ProductResult />} />
                <Route path='/home' element={<Home />} />
                <Route path='/login' element={<Login />} />
                <Route path='/signup' element={<Sign />} />
                <Route path="/" element={<Login />} />
                <Route path='/profilesetting' element={<Profile />} />
                <Route path='/profileedit' element={<ProfileEdit />} />
                <Route path='/profileview' element={<ProfileView />} />

            </Routes>
            
        </BrowserRouter>
    );
};

export default App;