import React, {Component} from 'react';
import { connect } from "react-redux";
import {userActions} from "../../actions";
import { Link } from 'react-router-dom';
import {AuthWrapper} from "./wrapper";
import {Spinner} from "../sub-components/spinner";

export class RecoverEmail extends Component {

    constructor(props){
        super(props);

        this.state = {
            email: '',
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
        const { email } = this.state;
        const { dispatch } = this.props;
        if (email) {
            dispatch(userActions.password_reset_request(email));
        }
    }

    render(){

        const { loggingIn } = this.props;
        const { email, submitted } = this.state;

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
                                    <label>Email Address</label>
                                    <input type="email" className="au-input au-input--full" name="email" value={email} onChange={this.handleChange} />
                                    {submitted && !email &&
                                    <div className="help-block">Email is required</div>
                                    }
                                </div>
                                <button class="au-btn au-btn--block au-btn--green m-b-20" type="submit"><Spinner loading={loggingIn}/> Send Password Reset</button>
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

const connectedRecoverEmailPage = connect(mapStateToProps)(RecoverEmail);
export { connectedRecoverEmailPage as RecoverEmailPage };