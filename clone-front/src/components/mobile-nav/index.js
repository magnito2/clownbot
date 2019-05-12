import React, {Component} from 'react';
import SlideToggle from "react-slide-toggle";

class MobileNavigation extends Component {

    constructor(props){
        super(props);
        this.state = {
            show_dropdown: false
        }
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(e) {
        e.preventDefault();
        this.setState({ show_dropdown: !this.state.show_dropdown });
    }

    render(){
        return <header class="header-mobile d-block d-lg-none">
            <SlideToggle>
                {({onToggle, setCollapsibleElement}) => (
                    <div className="mobile_collapsible">
                        <div class="header-mobile__bar">
                            <div class="container-fluid">
                                <div class="header-mobile-inner">
                                    <a class="logo" href="/">
                                        <img src="images/icon/clown.png" alt="Clown" />
                                    </a>
                                    <button class={"hamburger hamburger--slider mobile-collapsible__toggle"} onClick={onToggle} type="button">
                            <span class="hamburger-box">
                                <span class="hamburger-inner"></span>
                            </span>
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div className="mobile_collapsible__content" ref={setCollapsibleElement}>
                            <nav class="navbar-mobile mobile_collapsible__content-inner">
                                <div class="container-fluid">
                                    <ul class="navbar-mobile__list list-unstyled">
                                        <li>
                                            <a href="/"><i class="fas fa-tachometer-alt"></i>Dashboard</a>
                                        </li>
                                        <li>
                                            <a href="/settings">
                                                <i class="fas fa-chart-bar"></i>Settings</a>
                                        </li>
                                    </ul>
                                </div>
                            </nav>
                        </div>
                    </div>
                )}
            </SlideToggle>
        </header>
    }
}

export {MobileNavigation}