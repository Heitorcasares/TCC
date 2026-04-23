import { useState } from 'react'
import logo from 'C:/Users/CAMARGO/Downloads/libras-removebg-preview.png'
import './App.css'


function App() {
  
  return (
    <>
      <div class='nav'>
        <nav>
          <ul>
            <li><img src={logo} style={{width: "60px", height: "60px", paddingTop: "12px", margin: "0", float: "left"}}/></li>
            <li><h3><a href="#">Home</a></h3></li>
            <li><h3><a href="#">Comunidades</a></h3></li>
          </ul>
        </nav>
      </div>    
    </>
  )
}

export default App
