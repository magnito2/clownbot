import React, { Component } from 'react';
import { Notify } from 'react-redux-notify';

function AuthWrapper(props) {

    return (
        <body>
        <div class="page-wrapper">
            <div class="page-content--bge5">
                <div className="container">
                    <Notify/>
                    {props.children}
                </div>
            </div>
        </div>
        </body>
    );
}

export { AuthWrapper };