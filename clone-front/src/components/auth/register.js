import React, {Component} from 'react';
import { connect } from "react-redux";
import {userActions} from "../../actions";
import { Link } from 'react-router-dom';
import {AuthWrapper} from "./wrapper";

export class Register extends Component {

    constructor(props) {
        super(props);

        this.state = {
            user: {
                username:'',
                email: '',
                password: '',
                tg_address:''
            },
            submitted: false
        };

        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
        this.handleSocialLogin = this.handleSocialLogin.bind(this);
    }

    handleChange(event) {
        const { name, value } = event.target;
        const { user } = this.state;
        this.setState({
            user: {
                ...user,
                [name]: value
            }
        });
    }

    handleSocialLogin(data) {
        const { type, email, social_id, avatar, username } = data;
        const { dispatch } = this.props;
        dispatch(userActions.oauthlogin({type, email, social_id, avatar_url : avatar, username}))
    }

    handleSubmit(event) {
        event.preventDefault();

        this.setState({ submitted: true });
        const { user } = this.state;
        const { dispatch } = this.props;
        if (user.username && user.email && user.password) {
            dispatch(userActions.register(user));
        }
    }

    render(){

        const { registering  } = this.props;
        const { user, submitted } = this.state;

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
                                    <label>Username</label>
                                    <input type="text" className="au-input au-input--full" name="username" value={user.username} onChange={this.handleChange} />
                                    {submitted && !user.username &&
                                    <div className="help-block">Username is required</div>
                                    }
                                </div>
                                <div class="form-group">
                                    <label>Email Address</label>
                                    <input type="email" className="au-input au-input--full" name="email" value={user.email} onChange={this.handleChange} />
                                    {submitted && !user.email &&
                                    <div className="help-block">Email is required</div>
                                    }
                                </div>
                                <div class="form-group">
                                    <label>Password</label>
                                    <input type="password" className="au-input au-input--full" name="password" value={user.password} onChange={this.handleChange} />
                                    {submitted && !user.password &&
                                    <div className="help-block">Password is required</div>
                                    }
                                </div>
                                <div class="form-group">
                                    <label>Confirm Password</label>
                                    <input type="password" className="au-input au-input--full" name="password_confirm" value={user.password_confirm} onChange={this.handleChange} />
                                    {submitted && !user.password_confirm && user.password !== user.password_confirm &&
                                    <div className="help-block">Password Confirmation is required</div>
                                    }
                                </div>
                                <div class="login-checkbox">
                                    <label>
                                        <input type="checkbox" name="aggree"/>Agree the terms and policy
                                    </label>
                                </div>
                                <button class="au-btn au-btn--block au-btn--green m-b-20" type="submit">register</button>
                                {registering &&
                                <img src="data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA==" />
                                }
                            </form>
                            <div class="register-link">
                                <p>
                                    Already have account?
                                    <Link to="/login">Sign In</Link>
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
    const { registering } = state.authentication;
    return {
        registering
    };
}

const connectedRegisterPage = connect(mapStateToProps)(Register);
export { connectedRegisterPage as RegisterPage };