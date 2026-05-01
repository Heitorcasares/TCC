import { useState } from 'react'
import Home from './pages/Home/Home.jsx'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Login from './pages/Login/Login.jsx'
import Comunidades from './pages/Comunidades/Comunidades.jsx'
import Loader from './components/Loader.jsx'



function App() {

  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home/>}/>
          <Route path="/login" element={<Login/>}/>
          <Route path="/comunidades" element={<Comunidades/>}/>
        </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
