import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from 'src/api.service';
import { FormGroup,FormControl,FormBuilder} from '@angular/forms'
import { HttpClient } from '@angular/common/http';
import { data } from 'src/data';
@Component({
  selector: 'app-shipping',
  templateUrl: './shipping.component.html',
  styleUrls: ['./shipping.component.css']
})
export class ShippingComponent implements OnInit {
  shipping!:{
    distance: number,
    cost: number,
    location:string,
  }
  codes!: {"uuid":number,"code":string,"name":string}[]
  shippingForm!:FormGroup;
  selectedLocation!: string;
  locations!: {uuid:number, code: string, city:string, name: string, region:string,latitude:number,longitude:number}[];
  disableCalc!: boolean

  constructor(private router: Router,private apiService:ApiService,private fb:FormBuilder,private http: HttpClient) {
    this.disableCalc = true;
   }
  
  getCodes(){
    this.apiService.getshippingCodes()
    .subscribe(data => {
      this.codes=data;
    }) 
  }

  getCities(code:string,term:string){
    this.apiService.getCities(code,term)
    .subscribe(data => {
      this.locations = data
    })
  }

  suggestCities($event:Event){
    let location = (<HTMLInputElement>document.getElementById('location')).value;
    this.getCities(this.shippingForm.value.country.code,location)
    this.disableCalc = false
  }

  ngOnInit(): void {
    this.getCodes();
    this.shippingForm = this.fb.group({
      country: [null],
    });
    // this.codes = [{"uuid":26,"code":"au","name":"Australia"},{"uuid":27,"code":"at","name":"Austria"},{"uuid":28,"code":"br","name":"Brasil"},{"uuid":29,"code":"bg","name":"Bulgaria"},{"uuid":30,"code":"ca","name":"Canada"},{"uuid":31,"code":"cz","name":"Czech Republic"},{"uuid":32,"code":"dk","name":"Denmark"},{"uuid":33,"code":"fi","name":"Finland"},{"uuid":34,"code":"fr","name":"France"},{"uuid":35,"code":"de","name":"Germany"},{"uuid":50,"code":"gb","name":"Great Britain"},{"uuid":36,"code":"hu","name":"Hungary"},{"uuid":37,"code":"in","name":"India"},{"uuid":38,"code":"it","name":"Italy"},{"uuid":39,"code":"jp","name":"Japan"},{"uuid":40,"code":"nl","name":"Netherlands"},{"uuid":41,"code":"no","name":"Norway"},{"uuid":42,"code":"pt","name":"Portugal"},{"uuid":43,"code":"ro","name":"Romania"},{"uuid":44,"code":"ru","name":"Russia"},{"uuid":45,"code":"es","name":"Spain"},{"uuid":46,"code":"se","name":"Sweden"},{"uuid":47,"code":"ch","name":"Swiss"},{"uuid":48,"code":"tr","name":"Turkey"},{"uuid":49,"code":"us","name":"USA"}]
  }

  calcShipping(){
    this.shipping = {distance:0,cost:0,location:""}
    this.selectedLocation = (<HTMLInputElement>document.getElementById('location')).value;
    // this.apiService.calcShipping(this.selectedLocation.uuid).subscribe(
    //   data=>{
    //     console.log(data)
    //     this.shipping.distance = Number(data.distance)
    //     this.shipping.cost = Number(data.cost)
    //   }
    // )
    this.shipping.distance = 550
    this.shipping.cost = 14.99
    this.shipping.location = this.shippingForm.value.country.name + ' ' + this.selectedLocation
    console.log(this.shipping)
  }

  confirmShipping(){
    this.http.post<any>('/api/shipping/confirm/'+this.apiService.currentUser.uniqueid,this.shipping).subscribe(
      data=>{
        console.log(data)
        this.apiService.cart = data
      }
    )
    //this.apiService.cart.items.push({"qty":1,"sku":"SHIP","name":"Shipping to " + this.shipping.location,"price":this.shipping.cost,"subtotal":this.shipping.cost})
    //this.apiService.cart.total += this.shipping.cost
    this.router.navigate(['/', 'payment']);
  }
}
