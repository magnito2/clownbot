import React, {Component} from 'react';

class DropdownLink extends Component{
    constructor(props){
        super(props);
        this.state = {
            show_sub_menu: false
        }
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(e) {
        e.preventDefault();
        this.setState({ show_sub_menu: !this.state.show_sub_menu });
    }

    render(){
        return (
            <li class="has-sub">
            <a class="js-arrow" href="#" onClick={this.handleChange}>
                <i class={"fas "+ this.props.fa_class}></i>{this.props.title}
            </a>
                <ul class="list-unstyled navbar__sub-list js-sub-list" style={this.state.show_sub_menu? {display: 'block'}: {display: 'none'}}>
                    {this.props.children}
                </ul>
            </li>)
    }
}

export {DropdownLink}