import { useState } from 'react'
import logo from "C:/Users/heito/OneDrive/Área de Trabalho/TCC/Librargo/src/img/libras-removebg-preview.png"
import usuario from "C:/Users/heito/OneDrive/Área de Trabalho/TCC/Librargo/src/img/user-icon-in-trendy-flat-style-isolated-on-grey-background-user-symbol-for-your-web-site-design-logo-app-ui-illustration-eps10-free-vector-removebg-preview.png"
import './App.css'


function App() {
  
  return (
    <>
      <div class='nav'>
        <nav>
          <ul>
            <li><img src={logo} style={{width: "60px", height: "60px", paddingTop: "12px", margin: "0", float: "left", position: "relative", top: "7px"}}/></li>
            <li><h3><a href="#">Home</a></h3></li>
            <li><h3><a href="#">Comunidades</a></h3></li>
            <div class="pesquisa">
              <li><div class="group">
                    <svg viewBox="0 0 24 24" aria-hidden="true" class="search-icon">
                      <g>
                        <path
                          d="M21.53 20.47l-3.66-3.66C19.195 15.24 20 13.214 20 11c0-4.97-4.03-9-9-9s-9 4.03-9 9 4.03 9 9 9c2.215 0 4.24-.804 5.808-2.13l3.66 3.66c.147.146.34.22.53.22s.385-.073.53-.22c.295-.293.295-.767.002-1.06zM3.5 11c0-4.135 3.365-7.5 7.5-7.5s7.5 3.365 7.5 7.5-3.365 7.5-7.5 7.5-7.5-3.365-7.5-7.5z"
                        ></path>
                      </g>
                    </svg>

                    <input
                      id="query"
                      class="input"
                      type="search"
                      placeholder="Search..."
                      name="searchbar"
                    />
                  </div>
              </li>
            </div>
            <li><img src={usuario}  style={{width: "80px", height: "80px", paddingBottom: "3px", margin: "0", float: "right", position: "relative", left: "150px", bottom: "5px"}}/></li>
          </ul>
        </nav>
      </div>

      <h1>Bem-vindo ao Librargo!</h1>
      <center><button class="button type1">
        <span class="btn-txt">Começar</span>
      </button></center>
 
    </>
  )
}

export default App
