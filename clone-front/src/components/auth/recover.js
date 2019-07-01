import React, {Component} from 'react';
import { connect } from "react-redux";
import {userActions, alertActions} from "../../actions";
import { Link } from 'react-router-dom';
import {AuthWrapper} from "./wrapper";
import {Spinner} from "../sub-components/spinner";

export class Recover extends Component {

    constructor(props){
        super(props);

        this.state = {
            password: '',
            password_confirm: '',
            token: '',
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
        const { password, token, password_confirm } = this.state;
        const { dispatch } = this.props;
        if (password && token && password === password_confirm) {
            dispatch(userActions.reset_password(password, token));
        }
        if (password_confirm !== password){
            dispatch(alertActions.error("The password should match the password confirmation"));
        }
    }

    componentDidMount(){
        this.setState({
            token: this.props.match.params.reset_token
        });
    }

    render(){

        const { loggingIn } = this.props;
        const { password, password_confirm, submitted } = this.state;
        return (
            <AuthWrapper>
                <div class="login-wrap">
                    <div class="login-content">
                        <div class="login-logo">
                            <a href="#">
                                <img src="images/icon/clown.png" alt="Clown Bot"/>
                            </a>
                        </div>
                        <div class="login-form">
                            <form onSubmit={this.handleSubmit}>
                                <div class="form-group">
                                    <label>Password</label>
                                    <input type="password" className="au-input au-input--full" name="password" value={password} onChange={this.handleChange} />
                                    {submitted && !password &&
                                    <div className="help-block">Password is required</div>
                                    }
                                </div>
                                <div class="form-group">
                                    <label>Confirm Password</label>
                                    <input type="password" className="au-input au-input--full" name="password_confirm" value={password_confirm} onChange={this.handleChange} />
                                    {submitted && !password_confirm && password !== password_confirm &&
                                    <div className="help-block">Password Confirmation Should be same as password</div>
                                    }
                                </div>
                                <button class="au-btn au-btn--block au-btn--green m-b-20" type="submit"><Spinner loading={loggingIn}/> Reset Password</button>
                            </form>
                            <div class="register-link">
                                <p>
                                    Don't you have account?
                                    <Link to="/register">Sign Up Here</Link>
                                </p>
                                <p>
                                    <Link to="/login">Back to Login page</Link>
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

const connectedRecoverPage = connect(mapStateToProps)(Recover);
export { connectedRecoverPage as RecoverPage };