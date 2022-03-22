import { Component } from '@angular/core';
import { User } from "../User";
import { Cart } from 'src/cart';
import {HttpClient} from '@angular/common/http';
import { ApiService } from '../api.service';
import { products } from 'src/products';
import { data } from 'src/data';
@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'robotshop-web';
  currentUser!: data
  products!: products[];
  categories!: any;
  searchText!: string
  searchResults!: {}

  user !: User
  cart!:Cart
  uniqueid!:{"uuid":""}

  constructor(private http : HttpClient,private apiService:ApiService){
  }

  ngOnInit(): void {
    this.http.get('/api/catalogue/categories')
    .subscribe(Response => {
      this.categories=Response;
    });
    if (this.apiService.loggedIn==false){
        this.user = {
          name: "anonymous",
          email: "anonymous@gmail.com",
          password:"",
          password2: "",
        }
        this.apiService.currentUser = {
          uniqueid: "",
          user: this.user,
          cart: {total:0}
        }
        this.apiService.getUniqueId()
        .subscribe(data => {
          this.apiService.currentUser.uniqueid=String(data.uuid);
        })
        this.currentUser = this.apiService.currentUser
    }
    else{
      this.currentUser = this.apiService.currentUser
    }
}

  getProducts(cat:string){
    this.apiService.getProducts(cat)
    .subscribe(data => {
      this.products=data;
    }) 
  }

  search(text:string){
    this.http.get('/api/catalogue/search/'+ text)
    .subscribe(Response => {
      console.log(Response);
      this.searchResults= Response;
    });
  }

}
