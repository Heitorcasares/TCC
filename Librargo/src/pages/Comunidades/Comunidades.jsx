import { useEffect, useState } from 'react'
import { BrowserRouter, Link, Routes, Route, useNavigate } from 'react-router-dom'
import logo from "./../../img/libras-removebg-preview.png"
import usuario from "./../../img/user-icon-in-trendy-flat-style-isolated-on-grey-background-user-symbol-for-your-web-site-design-logo-app-ui-illustration-eps10-free-vector-removebg-preview.png"
import Loader from './../../components/Loader.jsx'
import Card from "./components/Card.jsx"
import Card_2 from "./components/Card_2.jsx"

export default function Comunidades() {
  
  const [ isLoading, setIsLoading ] = useState(false);
  
  const Login = () => {
    setIsLoading(true)
  }
  return (
    <>
      <div className='nav'>
        <nav>
          <ul>
            <li><Link to='/'><img src={logo} className="logo"/></Link></li>
            <li><h3><Link to="/" className="a">Home</Link></h3></li>
            <li><h3><Link to='/comunidades' className="a" onClick={Login}>Comunidades</Link></h3></li>
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

   <div>      
    <Card/>
    <Card_2/>
   </div>

      

      {isLoading && <Loader/>}
    </>
  )
}
