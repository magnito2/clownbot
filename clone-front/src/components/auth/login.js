import React, {Component} from 'react';
import { connect } from "react-redux";
import {userActions} from "../../actions";
import { Link } from 'react-router-dom';
import {AuthWrapper} from "./wrapper";
import {Spinner} from "../sub-components/spinner";

export class Login extends Component {

    constructor(props){
        super(props);

        // reset login status
        this.props.dispatch(userActions.logout());

        this.state = {
            email: '',
            password: '',
            submitted: false
        };

        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleChange(e) {
        const { name, value } = e.target;
        this.setState({ [name]: value });
    }

    handleSubmit(e) {
        e.preventDefault();

        this.setState({ submitted: true });
        const { email, password } = this.state;
        const { dispatch } = this.props;
        if (email && password) {
            dispatch(userActions.login(email, password));
        }
    }

    render(){

        const { loggingIn } = this.props;
        const { email, password, submitted } = this.state;

        return (
            <AuthWrapper>
                <div class="login-wrap">
                    <div class="login-content">
                        <div class="login-logo">
                            <a href="#">
                                <img src="images/icon/clown.png" alt="CoolAdmin"/>
                            </a>
                        </div>
                        <div class="login-form">
                            <form onSubmit={this.handleSubmit}>
                                <div class="form-group">
                                    <label>Email Address</label>
                                    <input type="email" className="au-input au-input--full" name="email" value={email} onChange={this.handleChange} />
                                    {submitted && !email &&
                                    <div className="help-block">Email is required</div>
                                    }
                                </div>
                                <div class="form-group">
                                    <label>Password</label>
                                    <input type="password" className="au-input au-input--full" name="password" value={password} onChange={this.handleChange} />
                                    {submitted && !password &&
                                    <div className="help-block">Password is required</div>
                                    }
                                </div>
                                <div class="login-checkbox">
                                    <label>
                                        <input type="checkbox" name="remember"/>Remember Me
                                    </label>
                                    <label>
                                        <a href="#">Forgotten Password?</a>
                                    </label>
                                </div>
                                <button class="au-btn au-btn--block au-btn--green m-b-20" type="submit"><Spinner loading={loggingIn}/> sign in</button>
                            </form>
                            <div class="register-link">
                                <p>
                                    Don't you have account?
                                    <Link to="/register">Sign Up Here</Link>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </AuthWrapper>
        );
    }
}

function mapStateToProps(state) {
    const { loggingIn } = state.authentication;
    return {
        loggingIn
    };
}

const connectedLoginPage = connect(mapStateToProps)(Login);
export { connectedLoginPage as LoginPage };