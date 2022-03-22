import { Component, OnInit } from '@angular/core';
import { Cart } from 'src/cart';
import { User } from 'src/User';
import { Router } from '@angular/router';
import { ApiService } from 'src/api.service';
import { data } from 'src/data';
@Component({
  selector: 'app-cart',
  templateUrl: './cart.component.html',
  styleUrls: ['./cart.component.css']
})
export class CartComponent implements OnInit {
  currentUser! : data;
  cart!: Cart;
  buttonDisabled!: boolean;

  constructor(private router: Router,private apiService:ApiService) { 
  }

  anonymous_user!: User;

  ngOnInit(): void {
  this.currentUser = this.apiService.currentUser
  this.cart = this.apiService.cart
  }

  buy(){
    // load shipping page
    this.router.navigate(['/', 'shipping']);
    // when buy done do totalcart as empty
  }

}
