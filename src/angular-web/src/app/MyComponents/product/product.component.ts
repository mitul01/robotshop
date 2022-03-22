import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import { Cart } from 'src/cart';
import { User } from 'src/User';
import { HttpClient } from '@angular/common/http';
import { products } from 'src/products';
import { ApiService } from 'src/api.service';
import { data } from 'src/data';

@Component({
  selector: 'app-product',
  templateUrl: './product.component.html',
  styleUrls: ['./product.component.css']
})

export class ProductComponent implements OnInit {
  sku!: string;
  message="";
  currentUser!: data;
  private sub: any;
  product!: products;
  rating!:{'avg_rating':number,'rating_count':number}
  quantity = 1;

  constructor(private route: ActivatedRoute,private http: HttpClient,private apiService:ApiService) {
    this.message = "";
    this.product = {_id:-1,sku:"",name:"",description:"",instock:-1,categories:[]}
    this.rating = {'avg_rating':0,'rating_count':0}
  }

  getItem(sku:string){
    this.apiService.getItem(sku)
    .subscribe(data => {
      this.product=data;
    }) 
  }

  loadRatings(sku:string){
    this.apiService.loadRatings(sku)
    .subscribe(data => {
      this.rating=data;
    }) 

  }

  ngOnInit(): void {
    this.sub = this.route.params.subscribe(params => {
    this.sku = String(params['sku']);
    this.getItem(this.sku)
    this.loadRatings(this.sku)
    this.message = ""
   });
   this.currentUser = this.apiService.currentUser;
  }

  addToCart(event:Event){
    this.apiService.addToCart(this.currentUser.uniqueid,this.sku,this.quantity).subscribe(data => {
      this.apiService.cart=data;
    })
    this.apiService.currentUser.cart.total += this.quantity
    this.message = "Added to cart"
  }

  rateProduct(vote:number){
    this.http.put<any>('/api/ratings/api/rate/' + this.sku + '/' + vote,{}).subscribe(
      data=>{
      }
      )
      this.message = "Thank you for your feedback"
  }

  glowstan(vote:number,val:number){
    var idx = vote;
    while(idx > 0) {
      (<HTMLInputElement>document.getElementById('vote-'+idx)).style.opacity = String(val);
        idx--;
    }
  }
}
