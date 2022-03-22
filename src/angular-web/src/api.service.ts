 
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { products } from './products';
import { data } from './data';
import { Cart } from './cart';
import { observableToBeFn } from 'rxjs/internal/testing/TestScheduler';

@Injectable({providedIn:'root'})
export class ApiService {

  currentUser!: data;
  cart!: Cart
  loggedIn!: boolean
  baseURL: string = "http://localhost:8080/";
  // baseURL: string = "/";
 
  constructor(private http: HttpClient) {
    this.loggedIn = false
  }
 
  getProducts(category:string): Observable<products[]> {
    return this.http.get<products[]>( this.baseURL + 'api/catalogue/products/' + category)
  }

  getItem(sku:string):Observable<products>{
    return this.http.get<products>( this.baseURL + 'api/catalogue/product/' + sku)
  }

  getUniqueId():Observable<{"uuid":""}>{
    return this.http.get<{"uuid":""}>( this.baseURL + 'api/user/uniqueid')
  }

  getSearchResults(text:string):Observable<{}>{
    return this.http.get<{}>(this.baseURL + 'api/catalogue/search' + text)
  }

  addToCart(uuid:string,sku:string,quantity:number):Observable<Cart>{
    return this.http.get<Cart>( this.baseURL + 'api/cart/add/' + uuid + '/' + sku + '/' + quantity)
  }

  loadCart(id:string):Observable<Cart>{
    return this.http.get<Cart>( this.baseURL + 'api/cart/cart/' + id)
  }

  loadRatings(sku:string):Observable<{'avg_rating':number,'rating_count':number}>{
    return this.http.get<{'avg_rating':number,'rating_count':number}>(this.baseURL + 'api/ratings/api/fetch/' + sku)
  }

  getshippingCodes():Observable<{"uuid":number,"code":string,"name":string}[]>{
    return this.http.get<{"uuid":number,"code":string,"name":string}[]>( this.baseURL + 'api/shipping/codes')
  }

  getCities(countryCode:string,term:string):Observable<{uuid:number, code: string, city:string, name: string, region:string,latitude:number,longitude:number}[]>{
    return this.http.get<{uuid:number, code: string, city:string, name: string, region:string,latitude:number,longitude:number}[]>(this.baseURL + '/api/shipping/match/'+ countryCode + '/' + term)
  }

  calcShipping(uuid:number):Observable<{distance:number,cost:number}>{
    return this.http.get<{distance:number,cost:number}>(this.baseURL + 'api/shipping/calc/'+ uuid)
  }

  getUserHistory(id:string):Observable<{_id:number,name:string,history:{cart:Cart,orderid:number}[]}>{
    return this.http.get<{_id:number,name:string,history:{cart:Cart,orderid:number}[]}>(this.baseURL + 'api/user/history/'+ id)
  }
 
}