import { useState } from 'react'
import { BrowserRouter, Link, Routes, Route, useNavigate } from 'react-router-dom'
import logo from "./../../img/libras-removebg-preview.png"
import usuario from "./../../img/user-icon-in-trendy-flat-style-isolated-on-grey-background-user-symbol-for-your-web-site-design-logo-app-ui-illustration-eps10-free-vector-removebg-preview.png"
import './Home.css'
import Login from '../Login.jsx'
import Comunidades from '../Comunidades.jsx'



function Home() {


  return (
    <>
      <div className='nav'>
        <nav>
          <ul>
            <li><Link to='/'><img src={logo} className="logo"/></Link></li>
            <li><h3><Link to="/" className="a">Home</Link></h3></li>
            <li><h3><Link to='/comunidades' className="a">Comunidades</Link></h3></li>
            <div className="pesquisa">
              <li><div className="group">
                    <svg viewBox="0 0 24 24" aria-hidden="true" className="search-icon">
                      <g>
                        <path
                          d="M21.53 20.47l-3.66-3.66C19.195 15.24 20 13.214 20 11c0-4.97-4.03-9-9-9s-9 4.03-9 9 4.03 9 9 9c2.215 0 4.24-.804 5.808-2.13l3.66 3.66c.147.146.34.22.53.22s.385-.073.53-.22c.295-.293.295-.767.002-1.06zM3.5 11c0-4.135 3.365-7.5 7.5-7.5s7.5 3.365 7.5 7.5-3.365 7.5-7.5 7.5-7.5-3.365-7.5-7.5z"
                        ></path>
                      </g>
                    </svg>
                    <input
                      id="query"
                      className="input"
                      type="search"
                      placeholder="Search..."
                      name="searchbar"
                    />
                  </div>
              </li>
            </div>
            <li><a href="#"><img src={usuario} className="usuario"/></a></li>
          </ul>
        </nav>
      </div>

      <h1>Bem-vindo ao Librargo!</h1>
      <center><Link to='/login'><button className="button type1">
        <span className="btn-txt">Começar</span>
      </button></Link></center>
    
    </>
  )
}

export default Home
