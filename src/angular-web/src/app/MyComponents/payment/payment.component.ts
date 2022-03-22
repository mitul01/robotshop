import { Component, OnInit } from '@angular/core';
import { Cart } from 'src/cart';
import {HttpClient} from '@angular/common/http';
import { ApiService } from 'src/api.service';
import { data } from 'src/data';
@Component({
  selector: 'app-payment',
  templateUrl: './payment.component.html',
  styleUrls: ['./payment.component.css']
})
export class PaymentComponent implements OnInit {
  totalcart!: Cart;
  currentUser!: data;
  subTotal!: number;
  tax!: number;
  message!: string;
  done!: boolean
  orderid!: string;

  constructor(private http : HttpClient,private apiService:ApiService) {
    this.done=false
   }

  ngOnInit(): void {
    this.totalcart = this.apiService.cart
    this.currentUser = this.apiService.currentUser
  }

  pay(){
    this.http.post<any>('/api/payment/pay/' + this.apiService.currentUser.uniqueid,this.apiService.cart).subscribe(
      data=>{
        this.orderid = data.orderid
      }
    )
    this.message = "Order Placed " + this.orderid
    this.apiService.cart = {
      total:0,
      tax:0,
      items: []
    }
    this.apiService.currentUser.cart.total = 0
    this.done = true
  }
}
