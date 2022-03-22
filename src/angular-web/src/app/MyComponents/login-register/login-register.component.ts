import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { User } from 'src/User';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { Cart } from 'src/cart';
import { HttpClient } from '@angular/common/http';
import { ApiService } from 'src/api.service';
@Component({
  selector: 'app-login-register',
  templateUrl: './login-register.component.html',
  styleUrls: ['./login-register.component.css']
})
export class LoginRegisterComponent implements OnInit {
  name!: string;
  email!: string;
  password!: string;
  password2!: string;
  login_name!:string;
  login_password!:string;
  loggedIn = false;
  totalCart!: Cart[];
  total!: number;
  message!: string;
  uniqueid!: {"uuid":""};
  history!: {_id:number,name:string,history:{cart:Cart,orderid:number}[]}

  constructor(private route: ActivatedRoute,private http: HttpClient,private apiService:ApiService) {
    this.message = ""
  }

  ngOnInit(): void {
    if(this.apiService.loggedIn==true){
      this.name = String(this.apiService.currentUser.user.name)
      this.email = String(this.apiService.currentUser.user.email)
      this.getHistory(this.apiService.currentUser.uniqueid)
      this.loggedIn = true;
    }
    this.message=""
  }

  register(event: Event){
    const user = {
      name: this.name,
      email: this.email,
      password: this.password,
      password2:this.password2,
      cartTotal: 0,
    }
    if (user.name && user.email && user.password && user.password2){
      if (user.password!=user.password2){
        this.message = "password dont match";
      }
      else{
        this.message = ""
        // post data to api
        this.http.post<{name:string,email:string,password:string}>('/api/user/register',
            {
            name:this.name,
            email:this.email,
            password:this.password
          }
        )
        this.apiService.currentUser = {
          uniqueid: user.name,
          user: user,
          cart: {total:0}
        }
        this.loggedIn = true;
        this.apiService.loggedIn = true;
        }
    }
    else{
      this.message = "fill all details";
    } 
  }

  login(event: Event){
    this.http.post<{name:string,password:string}>('/api/user/login',
    {
    name:this.login_name,
    password:this.login_password,
    }
  ).subscribe(
    (data)=>{
      console.log(data)
      // this.apiService.currentUser = data
    }
  )
  if (this.login_name && this.login_password){
    this.loggedIn = true
  }
  // this.http.get<{}>('/api/cart/rename/'+ this.apiService.currentUser.uniqueid + '/' + this.name )
  }

  getHistory(id:string){
    this.apiService.getUserHistory(id).subscribe(
      data=>{
        this.history = data
      }
    )
  }

  logout(){
    this.loggedIn = false;
    this.apiService.loggedIn = false;
  }

}
