import React from 'react';
import { useState } from 'react'
import { GoogleLogin, googleLogout } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import Loader from '../../../components/Loader';

function Form() {
  const [ isLoading, setIsLoading ] = useState(false);
      
  const Loading = () => {
    setIsLoading(true)
  }

  const handleLogout = () => {
    googleLogout()
  }

  const navigate = useNavigate()
  return (

    <>
      <StyledWrapper>
        <center>
          <form className="form">
            <div className="title">Welcome,<br /><span>sign up to continue</span></div>
            <input type="email" placeholder="Email" name="email" className="input" />
            <input type="password" placeholder="Password" name="password" className="input" />
            <div className="login-with">
              <div className="button-log"></div>
              <div className="button-log">
                <GoogleLogin onSuccess={(credentialResponse) => {
                  console.log(credentialResponse)
                  console.log(jwtDecode(credentialResponse.credential))
                  navigate("/comunidades")
                }} onError={() => console.log("Login failed!")} auto_select={true}/>
              </div>
              <div className="button-log">
                <svg xmlnsXlink="http://www.w3.org/1999/xlink" xmlns="http://www.w3.org/2000/svg" xmlSpace="preserve" width="56.693px" viewBox="0 0 56.693 56.693" version="1.1" id="Layer_1" height="56.693px" className="icon"><path d="M40.43,21.739h-7.645v-5.014c0-1.883,1.248-2.322,2.127-2.322c0.877,0,5.395,0,5.395,0V6.125l-7.43-0.029  c-8.248,0-10.125,6.174-10.125,10.125v5.518h-4.77v8.53h4.77c0,10.947,0,24.137,0,24.137h10.033c0,0,0-13.32,0-24.137h6.77  L40.43,21.739z" /></svg>
              </div>
            </div>
            <button className="button-confirm" onClick={Loading}>Let`s go →</button>
          </form>
        </center>
      </StyledWrapper>
      {isLoading && <Loader/>}
    </>
  );
}

const StyledWrapper = styled.div`
  .form {
    --input-focus: #4f4f4fff;
    --font-color: rgb(255, 255, 255);
    --font-color-sub: #d6d6d6ff;
    --bg-color: #fff;
    --main-color: #323232;
    padding: 20px;
    background: cadetblue;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 20px;
    border-radius: 5px;
    border: 2px solid var(--main-color);
    box-shadow: 4px 4px var(--main-color);
    width: 20%;
    position: relative;
    top: 150px;
  }

  .title {
    color: var(--font-color);
    font-weight: 900;
    font-size: 20px;
    margin-bottom: 25px;
  }

  .title span {
    color: var(--font-color-sub);
    font-weight: 600;
    font-size: 17px;
  }

  .input {
    width: 250px;
    height: 40px;
    border-radius: 5px;
    border: 2px solid var(--main-color);
    background-color: var(--bg-color);
    box-shadow: 4px 4px var(--main-color);
    font-size: 15px;
    font-weight: 600;
    color: black;
    padding: 5px 10px;
    outline: none;
    display: flex;
  }

  .input::placeholder {
    color: black;
    opacity: 0.8;
  }

  .input:focus {
    border: 2px solid var(--input-focus);
  }

  .login-with {
    display: flex;
    gap: 20px;
  }

  .button-log {
    cursor: pointer;
    width: 40px;
    height: 40px;
    border-radius: 100%;
    border: 2px solid var(--main-color);
    background-color: var(--bg-color);
    box-shadow: 4px 4px var(--main-color);
    color: black;
    font-size: 25px;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .icon {
    width: 24px;
    height: 24px;
    fill: var(--main-color);
  }

  .button-log:active, .button-confirm:active {
    box-shadow: 0px 0px var(--main-color);
    transform: translate(3px, 3px);
  }

  .button-confirm {
    margin: 50px auto 0 auto;
    width: 120px;
    height: 40px;
    border-radius: 5px;
    border: 2px solid var(--main-color);
    background-color: var(--bg-color);
    box-shadow: 4px 4px var(--main-color);
    font-size: 17px;
    font-weight: 600;
    color: black;
    cursor: pointer;
  }`;

export default Form;
